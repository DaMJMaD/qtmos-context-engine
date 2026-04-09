from __future__ import annotations

import getpass
import hashlib
import json
import os
from pathlib import Path
from typing import Any

from .appender import append_event
from .models import now_iso
from .paths import PROJECT_ROOT


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def collect_privilege_observation(
    *,
    method: str = "sudo",
    result: str = "prompted",
    target_user: str = "root",
    target_uid: int | None = 0,
    reason: str = "",
    command: list[str] | None = None,
) -> dict[str, Any]:
    env = os.environ
    command = list(command or [])
    resolved_target_uid = None if target_uid is None or target_uid < 0 else int(target_uid)
    return {
        "method": str(method or "sudo").strip() or "sudo",
        "result": str(result or "prompted").strip() or "prompted",
        "target_user": str(target_user or "").strip(),
        "target_uid": resolved_target_uid,
        "reason": str(reason or "").strip(),
        "command": command,
        "command_text": " ".join(command),
        "capture_ts": now_iso(),
        "user": getpass.getuser(),
        "uid": os.getuid(),
        "euid": os.geteuid(),
        "pid": os.getpid(),
        "ppid": os.getppid(),
        "shell": env.get("SHELL", ""),
        "home": str(Path.home()),
        "cwd": str(Path.cwd()),
        "tty": env.get("XDG_VTNR", "") or env.get("TTY", ""),
        "session_type": env.get("XDG_SESSION_TYPE", ""),
        "current_desktop": env.get("XDG_CURRENT_DESKTOP", ""),
        "display": env.get("DISPLAY", ""),
        "wayland_display": env.get("WAYLAND_DISPLAY", ""),
    }


def build_privilege_event(
    *,
    method: str = "sudo",
    result: str = "prompted",
    target_user: str = "root",
    target_uid: int | None = 0,
    reason: str = "",
    command: list[str] | None = None,
) -> dict[str, Any]:
    observation = collect_privilege_observation(
        method=method,
        result=result,
        target_user=target_user,
        target_uid=target_uid,
        reason=reason,
        command=command,
    )
    return {
        "type": "privilege.observe",
        "kind": "privilege.observe",
        "subject": "privilege.observe",
        "source": {
            "host": "privilege-observer",
            "workspace": str(PROJECT_ROOT),
            "session": "desktop-local",
            "observer": f"{observation.get('method')}-boundary",
        },
        "payload": {
            "privilege_observation": observation,
            "privilege_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(
                    {
                        "method": observation.get("method"),
                        "result": observation.get("result"),
                        "target_user": observation.get("target_user"),
                        "target_uid": observation.get("target_uid"),
                        "command_text": observation.get("command_text"),
                        "user": observation.get("user"),
                        "uid": observation.get("uid"),
                        "euid": observation.get("euid"),
                    }
                ),
                "stable_keys": [
                    "method",
                    "result",
                    "target_user",
                    "target_uid",
                    "command_text",
                    "user",
                    "uid",
                    "euid",
                ],
            },
        },
        "tags": [
            "privilege_boundary",
            f"privilege_method:{observation.get('method')}",
            f"privilege_result:{observation.get('result')}",
        ]
        + ([f"privilege_target:{observation.get('target_user')}"] if observation.get("target_user") else [])
        + (
            ["privilege_granted"]
            if observation.get("result") == "granted"
            else ["privilege_denied"]
            if observation.get("result") == "denied"
            else []
        ),
    }


def observe_privilege_and_cycle(
    *,
    method: str = "sudo",
    result: str = "prompted",
    target_user: str = "root",
    target_uid: int | None = 0,
    reason: str = "",
    command: list[str] | None = None,
) -> dict[str, Any]:
    from .project_busydawg import project_busydawg
    from .project_tags import project_tags
    from .rebuild_state import rebuild_state

    event = append_event(
        build_privilege_event(
            method=method,
            result=result,
            target_user=target_user,
            target_uid=target_uid,
            reason=reason,
            command=command,
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
