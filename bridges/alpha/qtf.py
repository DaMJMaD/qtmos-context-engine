from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

from .appender import append_event
from .models import now_iso
from .paths import PROJECT_ROOT


DEFAULT_QTF_IMAGE = "ubuntu:latest"
DEFAULT_QTF_LABEL = "local-offline-cage"
DEFAULT_QTF_TIMEOUT_SECONDS = 45


def _payload_hash(payload: dict[str, Any]) -> str:
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def _command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _snapshot_workspace(root: Path) -> dict[str, dict[str, Any]]:
    snapshot: dict[str, dict[str, Any]] = {}
    if not root.exists():
        return snapshot

    for item in sorted(root.rglob("*")):
        relative = item.relative_to(root).as_posix()
        if item.is_symlink():
            snapshot[relative] = {"kind": "symlink", "target": os.readlink(item)}
            continue
        if item.is_file():
            stat = item.stat()
            snapshot[relative] = {
                "kind": "file",
                "size": stat.st_size,
                "sha256": _hash_file(item),
            }
    return snapshot


def _diff_snapshots(
    before: dict[str, dict[str, Any]],
    after: dict[str, dict[str, Any]],
) -> dict[str, list[str]]:
    before_keys = set(before)
    after_keys = set(after)
    created = sorted(after_keys - before_keys)
    deleted = sorted(before_keys - after_keys)
    modified = sorted(
        path for path in before_keys & after_keys if before[path] != after[path]
    )
    return {
        "created_files": created,
        "modified_files": modified,
        "deleted_files": deleted,
    }


def _prepare_workspace(seed_path: str | None) -> tuple[Path, Path, str, str, dict[str, dict[str, Any]]]:
    temp_root = Path(tempfile.mkdtemp(prefix="qtmos-qtf-"))
    workspace_root = temp_root / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)

    workspace_seed = ""
    workspace_mode = "empty"

    if seed_path:
        source = Path(seed_path).expanduser().resolve()
        if not source.exists():
            raise FileNotFoundError(f"Workspace path does not exist: {source}")
        workspace_seed = str(source)
        if source.is_dir():
            workspace_mode = "directory"
            shutil.copytree(source, workspace_root, dirs_exist_ok=True)
        else:
            workspace_mode = "file"
            shutil.copy2(source, workspace_root / source.name)

    return temp_root, workspace_root, workspace_seed, workspace_mode, _snapshot_workspace(workspace_root)


def _build_bwrap_command(command: list[str], workspace_root: Path) -> list[str]:
    return [
        "bwrap",
        "--unshare-net",
        "--unshare-ipc",
        "--unshare-pid",
        "--unshare-uts",
        "--unshare-cgroup",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/var/tmp",
        "--tmpfs",
        "/home/qtf",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/etc",
        "/etc",
        "--ro-bind",
        "/opt",
        "/opt",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--bind",
        str(workspace_root),
        "/workspace",
        "--chdir",
        "/workspace",
        "--clearenv",
        "--setenv",
        "HOME",
        "/home/qtf",
        "--setenv",
        "NODE_ENV",
        "production",
        "--setenv",
        "PATH",
        "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "--die-with-parent",
        *command,
    ]


def _build_podman_command(command: list[str], workspace_root: Path, image: str) -> list[str]:
    return [
        "podman",
        "run",
        "--rm",
        "--pull=never",
        "--network",
        "none",
        "--read-only",
        "--tmpfs",
        "/tmp:rw,size=64m",
        "--tmpfs",
        "/var/tmp:rw,size=64m",
        "--tmpfs",
        "/home/qtf:rw,size=64m",
        "--security-opt",
        "no-new-privileges",
        "--cap-drop",
        "ALL",
        "--pids-limit",
        "256",
        "--userns",
        "keep-id",
        "--user",
        f"{os.getuid()}:{os.getgid()}",
        "-e",
        "HOME=/home/qtf",
        "-e",
        "NODE_ENV=production",
        "-e",
        "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "-w",
        "/workspace",
        "-v",
        f"{workspace_root}:/workspace:rw",
        image,
        *command,
    ]


@lru_cache(maxsize=1)
def probe_bwrap() -> tuple[bool, str]:
    if not _command_exists("bwrap"):
        return False, "bwrap not found"
    probe_cmd = [
        "bwrap",
        "--dev-bind",
        "/dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
        "--tmpfs",
        "/home/qtf",
        "--ro-bind",
        "/usr",
        "/usr",
        "--ro-bind",
        "/etc",
        "/etc",
        "--ro-bind",
        "/opt",
        "/opt",
        "--ro-bind",
        "/bin",
        "/bin",
        "--ro-bind",
        "/lib",
        "/lib",
        "--ro-bind",
        "/lib64",
        "/lib64",
        "--setenv",
        "HOME",
        "/home/qtf",
        "/usr/bin/true",
    ]
    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=5)
    except Exception as exc:
        return False, str(exc)
    if result.returncode == 0:
        return True, "ready"
    return False, (result.stderr or result.stdout or "bwrap probe failed").strip()


@lru_cache(maxsize=8)
def probe_podman(image: str = DEFAULT_QTF_IMAGE) -> tuple[bool, str]:
    if not _command_exists("podman"):
        return False, "podman not found"

    exists = subprocess.run(
        ["podman", "image", "exists", image],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if exists.returncode != 0:
        return False, f"podman image missing: {image}"

    probe = subprocess.run(
        ["podman", "run", "--rm", "--pull=never", "--network", "none", image, "/bin/true"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if probe.returncode == 0:
        return True, "ready"
    return False, (probe.stderr or probe.stdout or "podman probe failed").strip()


def select_qtf_backend(
    requested: str = "auto",
    *,
    image: str = DEFAULT_QTF_IMAGE,
) -> tuple[str, str]:
    requested = (requested or "auto").strip().lower()

    if requested == "bwrap":
        ok, note = probe_bwrap()
        if not ok:
            raise RuntimeError(f"QTF backend bwrap unavailable: {note}")
        return "bwrap", note

    if requested == "podman":
        ok, note = probe_podman(image)
        if not ok:
            raise RuntimeError(f"QTF backend podman unavailable: {note}")
        return "podman", note

    bwrap_ok, bwrap_note = probe_bwrap()
    if bwrap_ok:
        return "bwrap", bwrap_note

    podman_ok, podman_note = probe_podman(image)
    if podman_ok:
        return "podman", f"fallback:{podman_note}; bwrap_unavailable:{bwrap_note}"

    raise RuntimeError(
        "QTF backend unavailable: "
        f"bwrap={bwrap_note}; podman={podman_note}"
    )


def build_qtf_event(execution: dict[str, Any]) -> dict[str, Any]:
    stable_observation = {
        "label": execution.get("label"),
        "backend": execution.get("backend"),
        "command_text": execution.get("command_text"),
        "workspace_seed": execution.get("workspace_seed"),
        "workspace_mode": execution.get("workspace_mode"),
        "success": execution.get("result", {}).get("success"),
        "exit_code": execution.get("result", {}).get("exit_code"),
    }
    backend = execution.get("backend", "unknown")
    success = bool(execution.get("result", {}).get("success", False))
    return {
        "type": "qtf.execution",
        "kind": "qtf.execution",
        "subject": "qtf.execution",
        "source": {
            "host": "qtf-runner",
            "workspace": str(PROJECT_ROOT),
            "session": "local-cage",
            "observer": f"qtf-{backend}",
        },
        "payload": {
            "qtf_execution": execution,
            "qtf_signature": {
                "signature_version": "v1",
                "content_hash": _payload_hash(stable_observation),
                "stable_keys": [
                    "label",
                    "backend",
                    "command_text",
                    "workspace_seed",
                    "workspace_mode",
                    "success",
                    "exit_code",
                ],
            },
        },
        "tags": [
            "qtf_execution",
            "containment",
            "offline_local",
            f"qtf_backend:{backend}",
            "qtf_success" if success else "qtf_failed",
        ],
    }


def _build_failed_execution(
    *,
    label: str,
    backend_requested: str,
    image: str,
    command: list[str],
    workspace: str | None,
    started_at: str,
    duration_ms: int,
    reason: str,
    workspace_mode: str = "error",
    backend: str = "unavailable",
) -> dict[str, Any]:
    return {
        "label": label or DEFAULT_QTF_LABEL,
        "backend_requested": backend_requested,
        "backend": backend,
        "backend_note": reason,
        "image": image if backend == "podman" or backend_requested == "podman" else "",
        "command": list(command),
        "command_text": " ".join(command),
        "workspace_seed": str(workspace or ""),
        "workspace_mode": workspace_mode,
        "sandbox_kept": False,
        "sandbox_root": "",
        "manifest": {
            "network": "disabled",
            "fake_home": "/home/qtf",
            "workspace_mount": "/workspace",
            "read_only_system": True,
            "tmpfs": ["/tmp", "/var/tmp", "/home/qtf"],
        },
        "result": {
            "success": False,
            "exit_code": -1,
            "duration_ms": duration_ms,
            "timed_out": False,
        },
        "artifacts": {
            "created_files": [],
            "modified_files": [],
            "deleted_files": [],
        },
        "stdout": "",
        "stderr": reason[:4000],
        "capture_ts": started_at,
    }


def run_qtf_command(
    *,
    command: list[str],
    label: str = DEFAULT_QTF_LABEL,
    backend: str = "auto",
    image: str = DEFAULT_QTF_IMAGE,
    workspace: str | None = None,
    timeout_seconds: int = DEFAULT_QTF_TIMEOUT_SECONDS,
    keep_sandbox: bool = False,
) -> dict[str, Any]:
    if not command:
        return {"status": "error", "reason": "no command provided"}

    started_at = now_iso()
    started_monotonic = time.monotonic()

    try:
        temp_root, workspace_root, workspace_seed, workspace_mode, before_snapshot = _prepare_workspace(workspace)
    except Exception as exc:
        execution = _build_failed_execution(
            label=label,
            backend_requested=backend,
            image=image,
            command=command,
            workspace=workspace,
            started_at=started_at,
            duration_ms=int((time.monotonic() - started_monotonic) * 1000),
            reason=str(exc),
        )
        event = append_event(build_qtf_event(execution))
        return {
            "status": "error",
            "reason": str(exc),
            "event_id": event.get("id"),
            "execution": execution,
        }

    selected_backend = ""
    backend_note = ""
    process: subprocess.CompletedProcess[str] | None = None
    timed_out = False
    runtime_error = ""

    try:
        selected_backend, backend_note = select_qtf_backend(backend, image=image)
        if selected_backend == "bwrap":
            runner = _build_bwrap_command(command, workspace_root)
        else:
            runner = _build_podman_command(command, workspace_root, image)

        try:
            process = subprocess.run(
                runner,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            runtime_error = "QTF execution timed out"
            process = subprocess.CompletedProcess(
                args=runner,
                returncode=-1,
                stdout=exc.stdout or "",
                stderr=((exc.stderr or "") + "\nQTF timeout").strip(),
            )
    except Exception as exc:
        runtime_error = str(exc)

    duration_ms = int((time.monotonic() - started_monotonic) * 1000)
    after_snapshot = _snapshot_workspace(workspace_root)
    file_changes = _diff_snapshots(before_snapshot, after_snapshot)

    success = bool(process and process.returncode == 0 and not timed_out and not runtime_error)
    execution = {
        "label": label or DEFAULT_QTF_LABEL,
        "backend_requested": backend,
        "backend": selected_backend or "unavailable",
        "backend_note": backend_note or runtime_error or "",
        "image": image if (selected_backend or backend) == "podman" else "",
        "command": list(command),
        "command_text": " ".join(command),
        "workspace_seed": workspace_seed,
        "workspace_mode": workspace_mode,
        "sandbox_kept": bool(keep_sandbox),
        "sandbox_root": str(temp_root) if keep_sandbox else "",
        "manifest": {
            "network": "disabled",
            "fake_home": "/home/qtf",
            "workspace_mount": "/workspace",
            "read_only_system": True,
            "tmpfs": ["/tmp", "/var/tmp", "/home/qtf"],
        },
        "result": {
            "success": success,
            "exit_code": process.returncode if process else -1,
            "duration_ms": duration_ms,
            "timed_out": timed_out,
        },
        "artifacts": file_changes,
        "stdout": (process.stdout if process else "")[:4000],
        "stderr": ((process.stderr if process else runtime_error) or "")[:4000],
        "capture_ts": started_at,
    }

    if not keep_sandbox:
        shutil.rmtree(temp_root, ignore_errors=True)

    if not selected_backend:
        event = append_event(build_qtf_event(execution))
        return {
            "status": "error",
            "reason": runtime_error or "no usable QTF backend",
            "event_id": event.get("id"),
            "execution": execution,
        }

    event = append_event(build_qtf_event(execution))
    return {
        "status": "executed",
        "event_id": event.get("id"),
        "qtf_success": success,
        "execution": execution,
    }
