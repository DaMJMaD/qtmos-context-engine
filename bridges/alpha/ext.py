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


def collect_ext_observation(
    *,
    result: str = "requested",
    target: str = "host",
    artifact_kind: str = "package",
    qtf_label: str = "",
    package_name: str = "",
    package_manager: str = "",
    reason: str = "",
) -> dict[str, Any]:
    env = os.environ
    return {
        "result": str(result or "requested").strip() or "requested",
        "target": str(target or "host").strip() or "host",
        "artifact_kind": str(artifact_kind or "package").strip() or "package",
        "qtf_label": str(qtf_label or "").strip(),
        "package_name": str(package_name or "").strip(),
        "package_manager": str(package_manager or "").strip(),
        "reason": str(reason or "").strip(),
        "capture_ts": now_iso(),
        "user": getpass.getuser(),
        "uid": os.getuid(),
        "cwd": str(Path.cwd()),
        "shell": env.get("SHELL", ""),
        "session_type": env.get("XDG_SESSION_TYPE", ""),
        "current_desktop": env.get("XDG_CURRENT_DESKTOP", ""),
        "display": env.get("DISPLAY", ""),
        "wayland_display": env.get("WAYLAND_DISPLAY", ""),
    }


def build_ext_event(
    *,
    result: str = "requested",
    target: str = "host",
    artifact_kind: str = "package",
    qtf_label: str = "",
    package_name: str = "",
    package_manager: str = "",
    reason: str = "",
) -> dict[str, Any]:
    observation = collect_ext_observation(
        result=result,
        target=target,
        artifact_kind=artifact_kind,
        qtf_label=qtf_label,
        package_name=package_name,
        package_manager=package_manager,
        reason=reason,
    )
    return {
        "type": "ext.promotion.observe",
        "kind": "ext.promotion.observe",
        "subject": "ext.promotion.observe",
        "source": {
            "host": "ext-gate",
            "workspace": str(PROJECT_ROOT),
            "session": "desktop-local",
            "observer": "ext-promotion-gate",
        },
        "payload": {
            "ext_observation": observation,
            "ext_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(
                    {
                        "result": observation.get("result"),
                        "target": observation.get("target"),
                        "artifact_kind": observation.get("artifact_kind"),
                        "qtf_label": observation.get("qtf_label"),
                        "package_name": observation.get("package_name"),
                        "package_manager": observation.get("package_manager"),
                        "user": observation.get("user"),
                        "uid": observation.get("uid"),
                    }
                ),
                "stable_keys": [
                    "result",
                    "target",
                    "artifact_kind",
                    "qtf_label",
                    "package_name",
                    "package_manager",
                    "user",
                    "uid",
                ],
            },
        },
        "tags": [
            "ext_promotion",
            f"ext_result:{observation.get('result')}",
            f"ext_target:{observation.get('target')}",
            f"ext_artifact:{observation.get('artifact_kind')}",
        ]
        + ([f"ext_qtf:{observation.get('qtf_label')}"] if observation.get("qtf_label") else [])
        + ([f"package_manager:{observation.get('package_manager')}"] if observation.get("package_manager") else [])
        + ([f"package_name:{observation.get('package_name')}"] if observation.get("package_name") else []),
    }


def observe_ext_and_cycle(
    *,
    result: str = "requested",
    target: str = "host",
    artifact_kind: str = "package",
    qtf_label: str = "",
    package_name: str = "",
    package_manager: str = "",
    reason: str = "",
) -> dict[str, Any]:
    from .project_busydawg import project_busydawg
    from .project_tags import project_tags
    from .rebuild_state import rebuild_state

    event = append_event(
        build_ext_event(
            result=result,
            target=target,
            artifact_kind=artifact_kind,
            qtf_label=qtf_label,
            package_name=package_name,
            package_manager=package_manager,
            reason=reason,
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
