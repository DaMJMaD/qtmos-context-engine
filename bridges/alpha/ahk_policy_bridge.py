from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .mindseye import resolve_mindseye_share_root
from .models import now_iso


DEFAULT_POLICY_CHANNEL = "ahk-policy"


def _channel_dir(share_root: Path, channel: str) -> Path:
    path = share_root / channel
    path.mkdir(parents=True, exist_ok=True)
    return path


def _latest_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "latest.json"


def _events_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "events.jsonl"


def _load_existing_payload(latest_path: Path) -> dict[str, Any]:
    if not latest_path.exists():
        return {}
    try:
        envelope = json.loads(latest_path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    payload = envelope.get("payload")
    return payload if isinstance(payload, dict) else {}


def _hook_id(payload: dict[str, Any]) -> str:
    stable = {
        "action": payload.get("action"),
        "policy_rule": payload.get("policy_rule"),
        "reason": payload.get("reason"),
        "summary": payload.get("summary"),
        "surface_id": payload.get("surface_id"),
        "web_origin": payload.get("web_origin"),
        "context_condition": payload.get("context_condition"),
        "applied_at": payload.get("applied_at"),
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"hook_{digest[:12]}"


def build_ahk_policy_envelope(report: dict[str, Any]) -> dict[str, Any]:
    policy = report.get("policy") or {}
    surface = report.get("active_surface") or {}
    web = report.get("active_web") or {}
    mindseye = report.get("active_mindseye") or {}
    binding = report.get("binding") or {}

    payload = {
        "hook_id": "",
        "action": policy.get("action", "warn"),
        "ui_hint": policy.get("action", "warn"),
        "policy_rule": policy.get("policy_rule", "default_fallback"),
        "reason": policy.get("reason", ""),
        "overall_status": report.get("overall_status", "unknown"),
        "summary": report.get("summary", ""),
        "applied_at": policy.get("applied_at") or report.get("timing", {}).get("rebuilt_at") or now_iso(),
        "surface_id": surface.get("surface_id"),
        "surface_title": surface.get("title"),
        "surface_process_name": surface.get("process_name"),
        "web_origin": web.get("origin"),
        "web_title": web.get("title"),
        "web_trust": web.get("web_trust"),
        "context_condition": mindseye.get("condition"),
        "context_stage": mindseye.get("stage"),
        "binding_confidence": binding.get("link_confidence", "none"),
        "binding_used_in_trust": bool(binding.get("binding_used_in_trust", False)),
        "trust_reasons": binding.get("trust_reasons", []),
        "match_signals": binding.get("match_signals", []),
        "mismatch_signals": binding.get("mismatch_signals", []),
    }
    payload["mindseye_condition"] = payload["context_condition"]
    payload["mindseye_stage"] = payload["context_stage"]
    payload["severity"] = _severity_for_action(payload["action"])
    payload["hook_id"] = _hook_id(payload)

    return {
        "ts": now_iso(),
        "channel": DEFAULT_POLICY_CHANNEL,
        "source": "QTMoSAlpha",
        "subject": "policy_action",
        "payload": payload,
    }


def _severity_for_action(action: str | None) -> str:
    normalized = (action or "").lower()
    if normalized == "warn":
        return "low"
    if normalized == "review":
        return "medium"
    if normalized in {"quarantine", "deny"}:
        return "high"
    return "none"


def publish_ahk_policy_hook(
    report: dict[str, Any],
    *,
    share_root: str | None = None,
    channel: str = DEFAULT_POLICY_CHANNEL,
) -> dict[str, Any]:
    resolved_root = resolve_mindseye_share_root(share_root)
    envelope = build_ahk_policy_envelope(report)
    envelope["channel"] = channel
    latest_path = _latest_path(resolved_root, channel)
    events_path = _events_path(resolved_root, channel)
    existing_payload = _load_existing_payload(latest_path)
    if existing_payload.get("hook_id") == envelope["payload"]["hook_id"]:
        return {
            "status": "hook_unchanged",
            "share_root": str(resolved_root),
            "channel": channel,
            "latest_path": str(latest_path),
            "events_path": str(events_path),
            "hook_id": envelope["payload"]["hook_id"],
            "action": envelope["payload"]["action"],
            "policy_rule": envelope["payload"]["policy_rule"],
        }

    tmp_path = latest_path.with_suffix(".json.tmp")

    tmp_path.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(latest_path)
    with events_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(envelope, sort_keys=True) + "\n")

    return {
        "status": "hook_published",
        "share_root": str(resolved_root),
        "channel": channel,
        "latest_path": str(latest_path),
        "events_path": str(events_path),
        "hook_id": envelope["payload"]["hook_id"],
        "action": envelope["payload"]["action"],
        "policy_rule": envelope["payload"]["policy_rule"],
    }
