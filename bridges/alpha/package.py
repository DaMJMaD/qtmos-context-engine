from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .appender import append_event
from .models import now_iso
from .paths import PROJECT_ROOT
from .qtf import DEFAULT_QTF_IMAGE, DEFAULT_QTF_TIMEOUT_SECONDS, run_qtf_command


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _slug(value: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return text or "pkg"


def default_package_qtf_label(manager: str, operation: str, package_name: str = "") -> str:
    parts = [_slug(manager), _slug(operation)]
    if package_name:
        parts.append(_slug(package_name))
    return "pkg-" + "-".join(parts)


def build_package_install_event(
    *,
    manager: str,
    operation: str,
    package_name: str = "",
    version_spec: str = "",
    source_kind: str = "local",
    workspace_seed: str = "",
    command: list[str] | None = None,
    scripts_policy: str = "default",
    lockfile_state: str = "unknown",
    qtf_requested: bool = False,
    qtf_label: str = "",
    qtf_backend_preference: str = "auto",
    qtf_image: str = "",
) -> dict[str, Any]:
    command = list(command or [])
    observation = {
        "manager": manager,
        "operation": operation,
        "package_name": package_name,
        "version_spec": version_spec,
        "source_kind": source_kind,
        "workspace_seed": workspace_seed,
        "command": command,
        "command_text": " ".join(command),
        "scripts_policy": scripts_policy,
        "lockfile_state": lockfile_state,
        "qtf_requested": qtf_requested,
        "qtf_label": qtf_label,
        "qtf_backend_preference": qtf_backend_preference,
        "qtf_image": qtf_image,
        "capture_ts": now_iso(),
    }

    return {
        "type": "package.install.observe",
        "kind": "package.install.observe",
        "subject": "package.install.observe",
        "source": {
            "host": "package-observer",
            "workspace": str(PROJECT_ROOT),
            "session": "package-local",
            "observer": f"{manager}-observer",
        },
        "payload": {
            "package_observation": observation,
            "package_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(observation),
                "stable_keys": [
                    "manager",
                    "operation",
                    "package_name",
                    "version_spec",
                    "source_kind",
                    "workspace_seed",
                    "command_text",
                    "scripts_policy",
                    "lockfile_state",
                    "qtf_requested",
                    "qtf_label",
                ],
            },
        },
        "tags": [
            "package_install",
            f"package_manager:{manager}",
            f"package_operation:{operation}",
            f"package_source:{source_kind}",
            f"package_scripts:{scripts_policy}",
            f"package_lockfile:{lockfile_state}",
        ] + (["package_qtf_requested"] if qtf_requested else []),
    }


def observe_package_install(
    *,
    manager: str,
    operation: str,
    package_name: str = "",
    version_spec: str = "",
    source_kind: str = "local",
    workspace: str | None = None,
    command: list[str] | None = None,
    scripts_policy: str = "default",
    lockfile_state: str = "unknown",
    route_qtf: bool = False,
    qtf_label: str = "",
    qtf_backend: str = "auto",
    qtf_image: str = DEFAULT_QTF_IMAGE,
    timeout_seconds: int = DEFAULT_QTF_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    command = list(command or [])
    resolved_qtf_label = qtf_label or default_package_qtf_label(manager, operation, package_name)
    observed = append_event(
        build_package_install_event(
            manager=manager,
            operation=operation,
            package_name=package_name,
            version_spec=version_spec,
            source_kind=source_kind,
            workspace_seed=workspace or "",
            command=command,
            scripts_policy=scripts_policy,
            lockfile_state=lockfile_state,
            qtf_requested=route_qtf,
            qtf_label=resolved_qtf_label if route_qtf else "",
            qtf_backend_preference=qtf_backend if route_qtf else "auto",
            qtf_image=qtf_image if route_qtf else "",
        )
    )

    qtf_result: dict[str, Any] | None = None
    if route_qtf:
        if not command:
            return {
                "status": "error",
                "reason": "route_qtf requires a command after --",
                "package_event": observed,
            }
        qtf_result = run_qtf_command(
            command=command,
            label=resolved_qtf_label,
            backend=qtf_backend,
            image=qtf_image,
            workspace=workspace,
            timeout_seconds=timeout_seconds,
        )

    return {
        "status": "observed",
        "package_event": observed,
        "qtf_routed": bool(route_qtf),
        "qtf_result": qtf_result,
    }
