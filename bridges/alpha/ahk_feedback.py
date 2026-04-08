from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .appender import append_event
from .mindseye import resolve_mindseye_share_root
from .paths import AHK_FEEDBACK_CURSOR_JSON, PROJECT_ROOT, ensure_runtime_dirs


DEFAULT_AHK_FEEDBACK_CHANNEL = "ahk-feedback"


def _channel_dir(share_root: Path, channel: str) -> Path:
    return share_root / channel


def _events_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "events.jsonl"


def _latest_path(share_root: Path, channel: str) -> Path:
    return _channel_dir(share_root, channel) / "latest.json"


def _load_cursor(path: Path = AHK_FEEDBACK_CURSOR_JSON) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _write_cursor(data: dict[str, Any], path: Path = AHK_FEEDBACK_CURSOR_JSON) -> None:
    ensure_runtime_dirs()
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def build_ahk_feedback_event(
    envelope: dict[str, Any],
    *,
    share_root: Path,
    channel: str,
) -> dict[str, Any]:
    payload = dict(envelope.get("payload") or {})
    capture_ts = envelope.get("ts")
    channel_dir = _channel_dir(share_root, channel)

    observation = {
        "channel": envelope.get("channel", channel),
        "source": envelope.get("source", "QTMoSPolicyHook"),
        "subject": envelope.get("subject", "review_response"),
        "capture_ts": capture_ts,
        "observer": payload.get("observer", "QTMoSPolicyHook"),
        "original_hook_id": payload.get("original_hook_id"),
        "original_action": payload.get("original_action"),
        "original_rule": payload.get("original_rule"),
        "user_response": payload.get("user_response"),
        "surface_id": payload.get("surface_id"),
        "surface_title": payload.get("surface_title"),
        "web_origin": payload.get("web_origin"),
        "reason": payload.get("reason", ""),
        "context_condition": payload.get("context_condition", payload.get("mindseye_condition", "")),
        "summary": payload.get("summary", ""),
        "shared_root": str(share_root),
        "shared_channel_dir": str(channel_dir),
        "shared_latest_path": str(_latest_path(share_root, channel)),
    }

    return {
        "type": "ahk.feedback",
        "kind": "ahk.feedback",
        "subject": "ahk.feedback",
        "source": {
            "host": "ahk-feedback",
            "workspace": str(PROJECT_ROOT),
            "session": "shared-sync",
            "observer": observation["observer"],
        },
        "payload": {
            "feedback_observation": observation,
            "feedback_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(observation),
                "stable_keys": [
                    "channel",
                    "source",
                    "subject",
                    "original_hook_id",
                    "original_action",
                    "original_rule",
                    "user_response",
                    "surface_id",
                    "web_origin",
                ],
            },
        },
        "tags": ["human_feedback", "policy_feedback"],
    }


def ingest_ahk_feedback_events(
    *,
    share_root: str | None = None,
    channel: str = DEFAULT_AHK_FEEDBACK_CHANNEL,
    cursor_path: Path = AHK_FEEDBACK_CURSOR_JSON,
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

            appended = append_event(build_ahk_feedback_event(envelope, share_root=resolved_root, channel=channel))
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


def ingest_ahk_feedback_and_cycle(
    *,
    share_root: str | None = None,
    channel: str = DEFAULT_AHK_FEEDBACK_CHANNEL,
    cursor_path: Path = AHK_FEEDBACK_CURSOR_JSON,
) -> dict[str, Any]:
    from .project_busydawg import project_busydawg
    from .project_tags import project_tags
    from .rebuild_state import rebuild_state

    result = ingest_ahk_feedback_events(share_root=share_root, channel=channel, cursor_path=cursor_path)
    if result["status"] == "missing":
        return result

    state = rebuild_state()
    tags = project_tags()
    busydawg = project_busydawg()
    result["state"] = state
    result["tags"] = tags
    result["busydawg"] = busydawg
    return result
