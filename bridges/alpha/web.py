from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .appender import append_event
from .models import now_iso
from .paths import LATEST_STATE_JSON
from .project_busydawg import project_busydawg
from .project_tags import project_tags
from .rebuild_state import rebuild_state


BRAND_DOMAIN_HINTS = {
    "openai": ("openai.com", "chatgpt.com"),
    "chatgpt": ("openai.com", "chatgpt.com"),
    "google": ("google.com", "gmail.com", "youtube.com", "googleusercontent.com", "gstatic.com"),
    "microsoft": ("microsoft.com", "live.com", "outlook.com", "office.com", "office365.com", "microsoftonline.com"),
    "github": ("github.com", "githubassets.com", "githubusercontent.com"),
    "steam": ("steampowered.com", "steamcommunity.com", "steamstatic.com"),
    "bank": ("bank",),
    "paypal": ("paypal.com",),
    "apple": ("apple.com", "icloud.com"),
    "amazon": ("amazon.com", "amazonaws.com"),
}

TRUSTED_CONTAINER_DOMAINS = {
    "github.com": ("github",),
    "gitlab.com": ("gitlab",),
    "bitbucket.org": ("bitbucket",),
    "notion.so": ("notion",),
    "docs.google.com": ("google", "docs"),
    "drive.google.com": ("google", "drive"),
}

SENSITIVE_CUES = (
    "login",
    "log in",
    "sign in",
    "signin",
    "password",
    "verify",
    "payment",
    "wallet",
    "2fa",
    "two-factor",
    "recovery",
    "admin",
)

BROWSER_PROCESS_FAMILIES = {
    "chrome": ("chrome", "google-chrome", "chromium", "chromium-browser", "brave", "msedge", "microsoft-edge"),
    "chromium": ("chromium", "chromium-browser", "google-chrome", "chrome", "brave"),
    "firefox": ("firefox",),
    "edge": ("msedge", "microsoft-edge", "edge"),
    "brave": ("brave", "brave-browser"),
}


def _normalize_origin(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def _extract_domain(origin: str) -> str:
    parsed = urlparse(origin)
    return parsed.netloc.lower().split(":", 1)[0]


def _normalize_snippet(text: str) -> str:
    return " ".join((text or "").split())[:240]


def _title_family(title: str) -> str:
    return " ".join((title or "").lower().split())


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _title_tokens(value: str) -> set[str]:
    return {
        token
        for token in re.split(r"[^a-z0-9]+", _normalize_text(value))
        if token and len(token) > 2
    }


def _domain_matches_any(domain: str, candidates: tuple[str, ...]) -> bool:
    if not domain:
        return False
    for candidate in candidates:
        candidate = candidate.lower()
        if "." not in candidate:
            if candidate in domain:
                return True
            continue
        if domain == candidate or domain.endswith(f".{candidate}"):
            return True
    return False


def _container_anchor_cues(domain: str) -> set[str]:
    if not domain:
        return set()

    anchors: set[str] = set()
    for container_domain, cues in TRUSTED_CONTAINER_DOMAINS.items():
        if domain == container_domain or domain.endswith(f".{container_domain}"):
            anchors.update(cues)
    return anchors


def _host_identity_cues(domain: str, cues: set[str], *, sensitive: bool) -> set[str]:
    if not cues:
        return set()

    # On trusted content platforms, treat brand/entity words as page subject unless the
    # page also looks identity-sensitive (login, payment, recovery, admin, etc).
    if not sensitive:
        container_anchors = _container_anchor_cues(domain)
        if container_anchors:
            return cues & container_anchors

    return set(cues)


def _match_brand_cues(text: str) -> set[str]:
    lowered = _normalize_text(text)
    return {cue for cue in BRAND_DOMAIN_HINTS if cue in lowered}


def _has_sensitive_cue(text: str) -> bool:
    lowered = _normalize_text(text)
    return any(cue in lowered for cue in SENSITIVE_CUES)


def _browser_family(browser: str) -> tuple[str, ...]:
    normalized = _normalize_text(browser)
    return BROWSER_PROCESS_FAMILIES.get(normalized, (normalized,))


def _surface_matches_browser(browser: str, surface: dict[str, Any]) -> bool:
    candidates = _browser_family(browser)
    process_name = _normalize_text(surface.get("process_name", ""))
    process_path = _normalize_text(surface.get("process_path", ""))
    return any(candidate and (candidate in process_name or candidate in process_path) for candidate in candidates)


def _surface_title_matches(web_title: str, surface_title: str) -> bool:
    normalized_web = _normalize_text(web_title)
    normalized_surface = _normalize_text(surface_title)
    if not normalized_web or not normalized_surface:
        return False
    if normalized_web in normalized_surface or normalized_surface in normalized_web:
        return True
    web_tokens = _title_tokens(normalized_web)
    surface_tokens = _title_tokens(normalized_surface)
    if not web_tokens or not surface_tokens:
        return False
    overlap = len(web_tokens & surface_tokens)
    return overlap >= max(1, min(len(web_tokens), len(surface_tokens)) // 2)


def _parse_iso(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def _time_matches(capture_ts: str, surface_ts: str, max_delta_seconds: int = 2) -> bool:
    left = _parse_iso(capture_ts)
    right = _parse_iso(surface_ts)
    if not left or not right:
        return False
    return abs((left - right).total_seconds()) <= max_delta_seconds


def build_surface_binding(
    *,
    browser: str,
    web_title: str,
    capture_ts: str,
    surface_hint: dict[str, Any] | None = None,
    candidate_surface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    hint = surface_hint or {}
    surface = candidate_surface or {}
    binding = {
        "surface_id": surface.get("surface_id") or "",
        "window_title": surface.get("window_title") or hint.get("window_title") or "",
        "process_name": surface.get("process_name") or hint.get("process_name") or "",
        "process_path": surface.get("process_path") or "",
        "surface_ts": surface.get("ts"),
        "link_confidence": "none",
        "match_signals": [],
        "mismatch_signals": [],
    }

    if not surface:
        return binding

    process_match = _surface_matches_browser(browser, surface)
    title_match = _surface_title_matches(web_title, surface.get("window_title", ""))
    time_match = _time_matches(capture_ts, surface.get("ts", ""))
    focused_match = bool(surface.get("focused"))

    if process_match:
        binding["match_signals"].append("process_family_match")
    else:
        binding["mismatch_signals"].append("process_family_mismatch")

    if title_match:
        binding["match_signals"].append("title_overlap")
    elif web_title and surface.get("window_title"):
        binding["mismatch_signals"].append("title_mismatch")

    if time_match:
        binding["match_signals"].append("timestamp_proximity")

    if focused_match:
        binding["match_signals"].append("surface_focused")

    if process_match and title_match and time_match:
        binding["link_confidence"] = "high"
    elif process_match and (title_match or time_match):
        binding["link_confidence"] = "medium"
    elif title_match or time_match:
        binding["link_confidence"] = "low"

    return binding


def _content_hash(payload: dict[str, Any]) -> str:
    stable = {
        "origin": payload.get("origin"),
        "domain": payload.get("domain"),
        "url": payload.get("url"),
        "title": payload.get("title"),
        "text_snippet": payload.get("text_snippet"),
        "tab_id": payload.get("tab_id"),
        "window_id": payload.get("window_id"),
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _derive_trust_reasons(
    status: str,
    drift_flags: list[str],
    mismatch_flags: list[str],
) -> list[str]:
    reasons: list[str] = []
    if mismatch_flags:
        reasons.extend(mismatch_flags)
    if not reasons:
        reasons.extend(drift_flags)
    if not reasons:
        if status == "trusted":
            reasons.append("clean_web_observation")
        elif status == "unknown":
            reasons.append("insufficient_web_context")
    return reasons[:3]


def _web_trust_summary(
    status: str,
    trust_reasons: list[str],
    binding_used_in_trust: bool,
    binding: dict[str, Any],
) -> str:
    link_confidence = binding.get("link_confidence", "none")
    if status == "trusted" and binding_used_in_trust and link_confidence == "high":
        return "trusted: high-confidence browser/surface alignment"
    if status == "trusted":
        return "trusted: clean browser observation"
    if status == "shifted" and "binding_family_mismatch" in trust_reasons:
        return "shifted: browser content mismatches linked surface family"
    if status == "suspicious" and "sensitive_flow_low_trust" in trust_reasons:
        return "suspicious: sensitive flow on unrelated or weak identity domain"
    if status == "shifted":
        return "shifted: page claim and observed web identity diverged"
    return "unknown: insufficient browser evidence"


def load_previous_web(state_path: Path = LATEST_STATE_JSON) -> dict[str, Any] | None:
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return state.get("active_web")


def classify_web_trust(
    observation: dict[str, Any],
    previous_web: dict[str, Any] | None,
    candidate_surface: dict[str, Any] | None = None,
) -> tuple[str, list[str], list[str]]:
    drift_flags: list[str] = []
    mismatch_flags: list[str] = []

    if not observation.get("url") or not observation.get("origin") or not observation.get("domain"):
        mismatch_flags.append("weak_web_observation")
        return "unknown", drift_flags, mismatch_flags

    title = observation.get("title") or ""
    text_snippet = observation.get("text_snippet") or ""
    domain = observation.get("domain") or ""
    binding = observation.get("linked_surface") or {}
    title_cues = _match_brand_cues(title)
    text_cues = _match_brand_cues(text_snippet)
    sensitive = _has_sensitive_cue(title) or _has_sensitive_cue(text_snippet)
    title_host_cues = _host_identity_cues(domain, title_cues, sensitive=sensitive)
    text_host_cues = _host_identity_cues(domain, text_cues, sensitive=sensitive)
    link_confidence = binding.get("link_confidence", "none")
    binding_mismatch_signals = set(binding.get("mismatch_signals", []))
    surface_trust = (candidate_surface or {}).get("trust_status", "unknown")

    if not title and not text_snippet:
        mismatch_flags.append("weak_web_observation")
        return "unknown", drift_flags, mismatch_flags

    if "process_family_mismatch" in binding_mismatch_signals and link_confidence in {"high", "medium", "low"}:
        mismatch_flags.append("binding_family_mismatch")

    if title_host_cues and not any(_domain_matches_any(domain, BRAND_DOMAIN_HINTS[cue]) for cue in title_host_cues):
        mismatch_flags.append("title_domain_mismatch")

    if text_host_cues and not any(_domain_matches_any(domain, BRAND_DOMAIN_HINTS[cue]) for cue in text_host_cues):
        mismatch_flags.append("text_domain_mismatch")

    if observation.get("mutated"):
        drift_flags.append("dom_mutation_observed")

    if not previous_web:
        if mismatch_flags and sensitive:
            mismatch_flags.append("sensitive_flow_low_trust")
            return "suspicious", drift_flags, sorted(set(mismatch_flags))
        if mismatch_flags:
            return "shifted", drift_flags, sorted(set(mismatch_flags))
        if link_confidence == "high" and surface_trust == "trusted":
            drift_flags.append("bound_surface_alignment")
            return "trusted", sorted(set(drift_flags)), mismatch_flags
        return "unknown", drift_flags, mismatch_flags

    same_tab = observation.get("tab_id") == previous_web.get("tab_id")
    same_window = observation.get("window_id") == previous_web.get("window_id")
    same_origin = observation.get("origin") == previous_web.get("origin")
    same_domain = observation.get("domain") == previous_web.get("domain")
    same_title_family = _title_family(observation.get("title", "")) == _title_family(previous_web.get("title", ""))
    previous_snippet = previous_web.get("text_snippet", "")
    snippet_changed = _normalize_text(text_snippet) != _normalize_text(previous_snippet)

    if same_tab and same_window and same_origin and observation.get("mutated") and (not same_title_family or snippet_changed):
        drift_flags.append("post_load_identity_shift")

    if mismatch_flags and sensitive:
        mismatch_flags.append("sensitive_flow_low_trust")
        return "suspicious", sorted(set(drift_flags)), sorted(set(mismatch_flags))

    if mismatch_flags:
        return "shifted", sorted(set(drift_flags)), sorted(set(mismatch_flags))

    if same_tab and same_window and same_origin and same_domain and same_title_family and not observation.get("mutated"):
        return "trusted", drift_flags, mismatch_flags

    if same_tab and same_window and same_origin and not same_title_family:
        drift_flags.append("tab_title_changed")
        return "shifted", sorted(set(drift_flags)), mismatch_flags

    if same_tab and same_window and not same_origin:
        drift_flags.append("tab_origin_changed")
        return "shifted", sorted(set(drift_flags)), mismatch_flags

    if not same_tab:
        drift_flags.append("active_tab_changed")
        return "trusted", sorted(set(drift_flags)), mismatch_flags

    if link_confidence == "high" and surface_trust == "trusted":
        drift_flags.append("bound_surface_alignment")
        return "trusted", sorted(set(drift_flags)), mismatch_flags

    return "unknown", sorted(set(drift_flags)), mismatch_flags


def build_web_event(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    browser: str,
    url: str,
    title: str,
    text_snippet: str,
    tab_id: int,
    window_id: int,
    mutated: bool = False,
    visible: bool = True,
    linked_surface: dict[str, Any] | None = None,
    candidate_surface: dict[str, Any] | None = None,
    previous_web: dict[str, Any] | None = None,
) -> dict[str, Any]:
    origin = _normalize_origin(url)
    domain = _extract_domain(origin)
    capture_ts = now_iso()
    surface_binding = build_surface_binding(
        browser=browser,
        web_title=title or "",
        capture_ts=capture_ts,
        surface_hint=linked_surface,
        candidate_surface=candidate_surface,
    )
    observation = {
        "browser": browser,
        "url": url,
        "origin": origin,
        "domain": domain,
        "title": title or "",
        "text_snippet": _normalize_snippet(text_snippet),
        "tab_id": tab_id,
        "window_id": window_id,
        "mutated": bool(mutated),
        "visible": bool(visible),
        "capture_ts": capture_ts,
        "linked_surface": surface_binding,
    }
    trust_status, drift_flags, mismatch_flags = classify_web_trust(
        observation,
        previous_web,
        candidate_surface=candidate_surface,
    )
    binding_used_in_trust = (
        "bound_surface_alignment" in drift_flags or "binding_family_mismatch" in mismatch_flags
    )
    trust_reasons = _derive_trust_reasons(trust_status, drift_flags, mismatch_flags)
    trust_summary = _web_trust_summary(
        trust_status,
        trust_reasons,
        binding_used_in_trust,
        surface_binding,
    )
    return {
        "type": "web.observe",
        "kind": "web.observe",
        "subject": "web.active",
        "source": {
            "host": host,
            "workspace": workspace,
            "session": session,
            "observer": observer_id,
        },
        "payload": {
            "web_claim": {
                "browser": browser,
                "label": "active_tab",
            },
            "web_observation": observation,
            "web_signature": {
                "signature_version": "v1",
                "content_hash": _content_hash(observation),
                "stable_keys": [
                    "origin",
                    "domain",
                    "url",
                    "title",
                    "tab_id",
                    "window_id",
                ],
            },
            "trust_state": {
                "status": trust_status,
                "drift_flags": drift_flags,
                "mismatch_flags": mismatch_flags,
                "trust_reasons": trust_reasons,
                "binding_used_in_trust": binding_used_in_trust,
                "summary": trust_summary,
            },
        },
        "tags": ["web_observed", "browser_claim"],
    }


def append_web_event(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    browser: str,
    url: str,
    title: str,
    text_snippet: str,
    tab_id: int,
    window_id: int,
    mutated: bool = False,
    visible: bool = True,
    linked_surface: dict[str, Any] | None = None,
    candidate_surface: dict[str, Any] | None = None,
    previous_web: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_event(
        build_web_event(
            host=host,
            workspace=workspace,
            session=session,
            observer_id=observer_id,
            browser=browser,
            url=url,
            title=title,
            text_snippet=text_snippet,
            tab_id=tab_id,
            window_id=window_id,
            mutated=mutated,
            visible=visible,
            linked_surface=linked_surface,
            candidate_surface=candidate_surface,
            previous_web=previous_web,
        )
    )


def append_web_and_cycle(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    browser: str,
    url: str,
    title: str,
    text_snippet: str,
    tab_id: int,
    window_id: int,
    mutated: bool = False,
    visible: bool = True,
    linked_surface: dict[str, Any] | None = None,
    candidate_surface: dict[str, Any] | None = None,
    previous_web: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = append_web_event(
        host=host,
        workspace=workspace,
        session=session,
        observer_id=observer_id,
        browser=browser,
        url=url,
        title=title,
        text_snippet=text_snippet,
        tab_id=tab_id,
        window_id=window_id,
        mutated=mutated,
        visible=visible,
        linked_surface=linked_surface,
        candidate_surface=candidate_surface,
        previous_web=previous_web,
    )
    state = rebuild_state()
    tags = project_tags()
    busydawg = project_busydawg()
    return {
        "event": event,
        "state": state,
        "tags": tags,
        "busydawg": busydawg,
    }
