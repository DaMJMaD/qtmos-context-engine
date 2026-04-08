from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .appender import append_event
from .paths import MINDS_EYE_CURSOR_JSON, PROJECT_ROOT, ensure_runtime_dirs


DEFAULT_MINDSEYE_SHARE_ROOT = Path.home() / "qtmos-share"


def _discover_mindseye_share_root() -> Path:
    candidates = [
        DEFAULT_MINDSEYE_SHARE_ROOT,
        Path.home() / "Desktop" / "qtmos-share",
    ]
    desktop = Path.home() / "Desktop"
    if desktop.exists():
        try:
            candidates.extend(
                sorted(path for path in desktop.glob("*/*/qtmos-share") if path.is_dir())
            )
        except Exception:
            pass

    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return DEFAULT_MINDSEYE_SHARE_ROOT


def resolve_mindseye_share_root(explicit_root: str | None = None) -> Path:
    if explicit_root:
        return Path(explicit_root).expanduser().resolve()

    env_root = os.environ.get("QTMOS_SHARE_DIR", "").strip()
    if env_root:
        return Path(env_root).expanduser().resolve()

    return _discover_mindseye_share_root()


def _channel_dir(share_root: Path, channel: str) -> Path:
    return share_root / channel


def _events_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "events.jsonl"


def _latest_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "latest.json"


def _load_cursor(path: Path = MINDS_EYE_CURSOR_JSON) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cursor(data: dict[str, Any], path: Path = MINDS_EYE_CURSOR_JSON) -> None:
    ensure_runtime_dirs()
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _as_number(value: Any) -> float | None:
    try:
        if value in {"", None}:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int_or_default(value: Any, default: int) -> int:
    number = _as_number(value)
    if number is None:
        return default
    return int(number)


def _clean_windows_path(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""

    if text.startswith(("Z:\\", "Z:/")):
        text = text[3:]
        if not text.startswith(("\\", "/")):
            text = "/" + text

    text = text.replace("\\", "/")
    while "//" in text:
        text = text.replace("//", "/")

    prefix = "/" if text.startswith("/") else ""
    parts = [part for part in text.split("/") if part]
    deduped: list[str] = []
    for part in parts:
        if deduped and deduped[-1] == part:
            continue
        deduped.append(part)
    text = prefix + "/".join(deduped)
    return text


def _normalize_mindseye_payload(payload: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(payload)
    cleaned["focus_level"] = _as_int_or_default(cleaned.get("focus_level"), 50)
    cleaned["stress_level"] = _as_int_or_default(cleaned.get("stress_level"), 20)
    cleaned["intent_signal"] = str(
        cleaned.get("intent_signal")
        or cleaned.get("intent")
        or "unknown"
    ).strip() or "unknown"
    cleaned["image_dir"] = _clean_windows_path(cleaned.get("image_dir"))
    cleaned["thybody_path"] = _clean_windows_path(cleaned.get("thybody_path"))
    return cleaned


def _context_summary(payload: dict[str, Any]) -> str:
    condition = str(payload.get("condition") or "").strip().upper()
    stage = str(payload.get("stage") or "").strip().lower()
    intent = str(payload.get("intent_signal") or payload.get("intent") or "").strip().lower()
    raw_text = str(payload.get("raw_text") or "").strip()

    parts: list[str] = []
    if condition and condition not in {"UNKNOWN", "ERROR"}:
        parts.append(f"condition:{condition}")
    if stage:
        parts.append(f"stage:{stage}")
    if intent and intent != "unknown":
        parts.append(f"intent:{intent}")
    if parts:
        return " | ".join(parts)
    return raw_text


def _normalize_context_observer(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text.lower() in {"mind's eye", "mindseye"}:
        return "AHK Context"
    return text


def _normalize_context_subject(value: Any) -> str:
    text = str(value or "").strip().lower()
    if not text or text == "vitals":
        return "context"
    return text


def build_mindseye_binding(
    mindseye: dict[str, Any] | None,
    active_surface: dict[str, Any] | None,
    active_web: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mindseye = mindseye or {}
    active_surface = active_surface or {}
    active_web = active_web or {}

    condition = str(mindseye.get("condition") or "").upper()
    stage = str(mindseye.get("stage") or "")
    raw_text = str(mindseye.get("raw_text") or "").strip()
    focus_level = _as_number(mindseye.get("focus_level"))
    stress_level = _as_number(mindseye.get("stress_level"))
    intent_signal = str(mindseye.get("intent_signal") or mindseye.get("intent") or "").strip()

    score = 0
    reasons: list[str] = []
    mismatch_signals: list[str] = []

    if active_surface.get("surface_id"):
        score += 2
        reasons.append("active_surface_present")
    if active_surface.get("focused"):
        score += 1
        reasons.append("surface_focused")
    if raw_text or condition or intent_signal or focus_level is not None or stress_level is not None:
        score += 1
        reasons.append("context_signal_present")
    if condition and condition not in {"UNKNOWN", "ERROR"}:
        score += 1
        reasons.append("condition_signal_present")
    if stage:
        reasons.append(f"stage:{stage}")

    linked_surface = active_web.get("linked_surface") or {}
    if active_web.get("origin"):
        if linked_surface.get("surface_id") and linked_surface.get("surface_id") == active_surface.get("surface_id"):
            score += 1
            reasons.append("surface_web_alignment")
        elif linked_surface.get("surface_id") and active_surface.get("surface_id"):
            mismatch_signals.append("web_surface_mismatch")
        else:
            reasons.append("web_context_present")

        if active_web.get("trust_status") == "trusted":
            score += 1
            reasons.append("trusted_web_context")

    if score >= 5:
        confidence = "high"
    elif score >= 3:
        confidence = "medium"
    elif score >= 1:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "confidence": confidence,
        "linked_surface_id": active_surface.get("surface_id"),
        "linked_surface_title": active_surface.get("window_title"),
        "linked_process_name": active_surface.get("process_name"),
        "linked_web_origin": active_web.get("origin"),
        "linked_web_title": active_web.get("title"),
        "reasons": reasons,
        "mismatch_signals": mismatch_signals,
        "context": {
            "user_state": condition or "UNKNOWN",
            "context_summary": mindseye.get("context_summary") or _context_summary(mindseye),
            "stage": stage,
            "focus_level": mindseye.get("focus_level"),
            "stress_level": mindseye.get("stress_level"),
            "intent_signal": mindseye.get("intent_signal") or mindseye.get("intent"),
        },
    }


def build_mindseye_event(
    envelope: dict[str, Any],
    *,
    share_root: Path,
    channel: str,
) -> dict[str, Any]:
    payload = _normalize_mindseye_payload(envelope.get("payload") or {})
    capture_ts = envelope.get("ts")
    channel_dir = _channel_dir(share_root, channel)

    observation = {
        "channel": envelope.get("channel", channel),
        "source": envelope.get("source", "MindsEye"),
        "subject": _normalize_context_subject(envelope.get("subject", "context")),
        "capture_ts": capture_ts,
        "observer": _normalize_context_observer(payload.get("observer", "AHK Context")),
        "stage": payload.get("stage", "pulse"),
        "raw_text": payload.get("raw_text", ""),
        "context_summary": _context_summary(payload),
        "condition": payload.get("condition", ""),
        "focus_level": payload.get("focus_level", 50),
        "stress_level": payload.get("stress_level", 20),
        "intent_signal": payload.get("intent_signal", "unknown"),
        "shared_root": str(share_root),
        "shared_channel_dir": str(channel_dir),
        "shared_latest_path": str(_latest_path(share_root, channel)),
    }

    return {
        "type": "mindseye.vitals",
        "kind": "mindseye.vitals",
        "subject": "mindseye.vitals",
        "source": {
            "host": "mindseye-sync",
            "workspace": str(PROJECT_ROOT),
            "session": "shared-sync",
            "observer": observation["observer"],
        },
        "payload": {
            "mindseye_observation": observation,
            "raw_shared_payload": payload,
            "mindseye_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(observation),
                "stable_keys": [
                    "channel",
                    "source",
                    "subject",
                    "stage",
                    "raw_text",
                    "condition",
                    "focus_level",
                    "stress_level",
                    "intent_signal",
                ],
            },
        },
        "tags": ["ahk_context_observed", "human_context"],
    }


def ingest_mindseye_events(
    *,
    share_root: str | None = None,
    channel: str = "mindseye",
    cursor_path: Path = MINDS_EYE_CURSOR_JSON,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    resolved_root = resolve_mindseye_share_root(share_root)
    events_path = _events_path(resolved_root, channel)
    latest_path = _latest_path(resolved_root, channel)

    if not events_path.exists():
        return {
            "status": "missing",
            "imported": 0,
            "share_root": str(resolved_root),
            "channel": channel,
            "events_path": str(events_path),
            "latest_path": str(latest_path),
        }

    cursor = _load_cursor(cursor_path)
    current_size = events_path.stat().st_size
    previous_path = cursor.get("events_path")
    offset = int(cursor.get("offset", 0) or 0)
    if previous_path != str(events_path) or current_size < offset:
        offset = 0

    imported: list[dict[str, Any]] = []
    next_offset = offset
    with events_path.open("r", encoding="utf-8") as handle:
        handle.seek(offset)
        while True:
            line_start = handle.tell()
            raw_line = handle.readline()
            if not raw_line:
                next_offset = handle.tell()
                break

            clean = raw_line.strip()
            if not clean:
                next_offset = handle.tell()
                continue

            try:
                envelope = json.loads(clean)
            except json.JSONDecodeError:
                next_offset = line_start
                break

            appended = append_event(build_mindseye_event(envelope, share_root=resolved_root, channel=channel))
            imported.append(appended)
            next_offset = handle.tell()

    _write_cursor(
        {
            "events_path": str(events_path),
            "latest_path": str(latest_path),
            "offset": next_offset,
            "channel": channel,
            "share_root": str(resolved_root),
        },
        cursor_path,
    )

    return {
        "status": "imported" if imported else "idle",
        "imported": len(imported),
        "share_root": str(resolved_root),
        "channel": channel,
        "events_path": str(events_path),
        "latest_path": str(latest_path),
        "cursor_path": str(cursor_path),
        "event_ids": [item["id"] for item in imported],
    }


def ingest_mindseye_and_cycle(
    *,
    share_root: str | None = None,
    channel: str = "mindseye",
    cursor_path: Path = MINDS_EYE_CURSOR_JSON,
) -> dict[str, Any]:
    from .project_busydawg import project_busydawg
    from .project_tags import project_tags
    from .rebuild_state import rebuild_state

    result = ingest_mindseye_events(share_root=share_root, channel=channel, cursor_path=cursor_path)
    if result["status"] == "missing":
        return result

    state = rebuild_state()
    tags = project_tags()
    busydawg = project_busydawg()
    result["state"] = state
    result["tags"] = tags
    result["busydawg"] = busydawg
    return result
