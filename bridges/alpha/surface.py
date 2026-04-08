from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .appender import append_event
from .models import dump_json, now_iso
from .paths import LATEST_STATE_JSON
from .project_busydawg import project_busydawg
from .project_tags import project_tags
from .rebuild_state import rebuild_state


def _title_family(title: str) -> str:
    if not title:
        return ""
    lowered = title.lower()
    lowered = re.sub(r"https?://", "", lowered)
    lowered = re.sub(r"\s+", " ", lowered).strip()
    parts = [part.strip() for part in lowered.split(" - ") if part.strip()]
    if parts:
        lowered = parts[0]
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return lowered.strip()


def _surface_hash(observation: dict[str, Any]) -> str:
    stable = {
        "platform": observation.get("platform"),
        "surface_id": observation.get("surface_id"),
        "process_path": observation.get("process_path"),
        "window_class": observation.get("window_class"),
        "window_title": observation.get("window_title"),
    }
    digest = hashlib.sha256(json.dumps(stable, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def load_previous_surface(state_path: Path = LATEST_STATE_JSON) -> dict[str, Any] | None:
    if not state_path.exists():
        return None
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return state.get("active_surface")


def classify_surface_trust(
    observation: dict[str, Any],
    previous_surface: dict[str, Any] | None,
) -> tuple[str, list[str], list[str]]:
    drift_flags: list[str] = []
    mismatch_flags: list[str] = []

    if not observation.get("surface_id"):
        mismatch_flags.append("missing_surface_id")
    if not observation.get("process_name"):
        mismatch_flags.append("missing_process_name")
    if not observation.get("window_class"):
        mismatch_flags.append("missing_window_class")
    if not observation.get("window_title"):
        mismatch_flags.append("missing_window_title")

    if mismatch_flags:
        return "suspicious", drift_flags, mismatch_flags

    if not previous_surface:
        return "unknown", drift_flags, mismatch_flags

    prev_id = previous_surface.get("surface_id")
    prev_proc = previous_surface.get("process_name")
    prev_class = previous_surface.get("window_class")
    prev_title = previous_surface.get("window_title")

    same_id = observation.get("surface_id") == prev_id
    same_proc = observation.get("process_name") == prev_proc
    same_class = observation.get("window_class") == prev_class
    same_title_family = _title_family(observation.get("window_title", "")) == _title_family(prev_title or "")

    if same_id and same_proc and same_class and same_title_family:
        return "trusted", drift_flags, mismatch_flags

    if not same_id:
        drift_flags.append("focus_surface_changed")
        return "trusted", drift_flags, mismatch_flags

    if same_proc and same_class and not same_title_family:
        drift_flags.append("title_family_changed")
        return "shifted", drift_flags, mismatch_flags

    if same_id and same_proc and not same_class:
        drift_flags.append("window_class_changed")
        return "shifted", drift_flags, mismatch_flags

    if same_id and not same_proc:
        drift_flags.append("process_changed_on_same_surface")
        return "shifted", drift_flags, mismatch_flags

    return "trusted", drift_flags, mismatch_flags


def build_surface_event(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    host_kind: str,
    label: str,
    observation: dict[str, Any],
    previous_surface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    observation = dict(observation)
    if not observation.get("capture_ts"):
        observation["capture_ts"] = now_iso()
    trust_status, drift_flags, mismatch_flags = classify_surface_trust(observation, previous_surface)
    return {
        "type": "surface.observe",
        "kind": "surface.observe",
        "subject": "surface.active",
        "source": {
            "host": host,
            "workspace": workspace,
            "session": session,
            "observer": observer_id,
        },
        "payload": {
            "surface_claim": {
                "host_kind": host_kind,
                "label": label,
            },
            "surface_observation": observation,
            "surface_signature": {
                "signature_version": "v1",
                "surface_hash": _surface_hash(observation),
                "stable_keys": [
                    "platform",
                    "surface_id",
                    "process_path",
                    "window_class",
                    "window_title",
                ],
            },
            "trust_state": {
                "status": trust_status,
                "drift_flags": drift_flags,
                "mismatch_flags": mismatch_flags,
            },
        },
        "tags": ["surface_observed", "host_identity"],
    }


def append_surface_event(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    host_kind: str,
    label: str,
    observation: dict[str, Any],
    previous_surface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return append_event(
        build_surface_event(
            host=host,
            workspace=workspace,
            session=session,
            observer_id=observer_id,
            host_kind=host_kind,
            label=label,
            observation=observation,
            previous_surface=previous_surface,
        )
    )


def append_surface_and_cycle(
    *,
    host: str,
    workspace: str,
    session: str,
    observer_id: str,
    host_kind: str,
    label: str,
    observation: dict[str, Any],
    previous_surface: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = append_surface_event(
        host=host,
        workspace=workspace,
        session=session,
        observer_id=observer_id,
        host_kind=host_kind,
        label=label,
        observation=observation,
        previous_surface=previous_surface,
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
