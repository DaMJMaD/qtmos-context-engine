from __future__ import annotations

import getpass
import hashlib
import json
import os
import platform
import socket
from pathlib import Path
from typing import Any

from .appender import append_event
from .models import now_iso
from .paths import PROJECT_ROOT


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def collect_host_session_observation(
    *,
    stage: str = "gnome-handoff",
    compromise_suspected: bool = False,
    suspicion_note: str = "",
    recovery_hint: str = "observe_only",
) -> dict[str, Any]:
    env = os.environ
    return {
        "stage": stage,
        "capture_ts": now_iso(),
        "hostname": socket.gethostname(),
        "user": getpass.getuser(),
        "uid": os.getuid(),
        "shell": env.get("SHELL", ""),
        "home": str(Path.home()),
        "cwd": str(Path.cwd()),
        "platform": platform.platform(),
        "desktop_session": env.get("DESKTOP_SESSION", ""),
        "current_desktop": env.get("XDG_CURRENT_DESKTOP", ""),
        "session_type": env.get("XDG_SESSION_TYPE", ""),
        "session_id": env.get("XDG_SESSION_ID", ""),
        "display": env.get("DISPLAY", ""),
        "wayland_display": env.get("WAYLAND_DISPLAY", ""),
        "tty": env.get("XDG_VTNR", ""),
        "boot_id": _read_text(Path("/proc/sys/kernel/random/boot_id")),
        "machine_id_present": bool(_read_text(Path("/etc/machine-id"))),
        "compromise_suspected": bool(compromise_suspected),
        "suspicion_note": str(suspicion_note or "").strip(),
        "recovery_hint": str(recovery_hint or "observe_only").strip() or "observe_only",
    }


def build_host_session_event(
    *,
    stage: str = "gnome-handoff",
    compromise_suspected: bool = False,
    suspicion_note: str = "",
    recovery_hint: str = "observe_only",
) -> dict[str, Any]:
    observation = collect_host_session_observation(
        stage=stage,
        compromise_suspected=compromise_suspected,
        suspicion_note=suspicion_note,
        recovery_hint=recovery_hint,
    )
    return {
        "type": "host.session.observe",
        "kind": "host.session.observe",
        "subject": "host.session.observe",
        "source": {
            "host": "host-session",
            "workspace": str(PROJECT_ROOT),
            "session": "desktop-local",
            "observer": "gnome-session-breadcrumb",
        },
        "payload": {
            "host_session_observation": observation,
            "host_session_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(
                    {
                        "stage": observation.get("stage"),
                        "hostname": observation.get("hostname"),
                        "user": observation.get("user"),
                        "boot_id": observation.get("boot_id"),
                        "desktop_session": observation.get("desktop_session"),
                        "current_desktop": observation.get("current_desktop"),
                        "session_type": observation.get("session_type"),
                        "compromise_suspected": observation.get("compromise_suspected"),
                        "recovery_hint": observation.get("recovery_hint"),
                    }
                ),
                "stable_keys": [
                    "stage",
                    "hostname",
                    "user",
                    "boot_id",
                    "desktop_session",
                    "current_desktop",
                    "session_type",
                    "compromise_suspected",
                    "recovery_hint",
                ],
            },
        },
        "tags": [
            "host_session",
            f"host_stage:{observation.get('stage')}",
            f"host_session_type:{str(observation.get('session_type') or 'unknown').lower()}",
            "compromise_suspected" if compromise_suspected else "compromise_not_suspected",
            f"recovery_hint:{str(observation.get('recovery_hint') or 'observe_only').lower()}",
        ],
    }


def observe_host_session_and_cycle(
    *,
    stage: str = "gnome-handoff",
    compromise_suspected: bool = False,
    suspicion_note: str = "",
    recovery_hint: str = "observe_only",
) -> dict[str, Any]:
    from .project_busydawg import project_busydawg
    from .project_tags import project_tags
    from .rebuild_state import rebuild_state

    event = append_event(
        build_host_session_event(
            stage=stage,
            compromise_suspected=compromise_suspected,
            suspicion_note=suspicion_note,
            recovery_hint=recovery_hint,
        )
    )
    state = rebuild_state()
    tags = project_tags()
    busydawg = project_busydawg()
    return {
        "status": "observed",
        "event": event,
        "state": state,
        "tags": tags,
        "busydawg": busydawg,
    }
