from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .appender import append_event
from .ext import build_ext_event
from .host_session import build_host_session_event
from .models import normalize_event
from .package import build_package_install_event
from .paths import EXT_SCENARIOS_DIR, PACKAGE_SCENARIOS_DIR
from .project_busydawg import project_busydawg
from .project_busydawg import build_busydawg_projection
from .project_tags import build_tags
from .project_tags import project_tags
from .qtf import build_qtf_event
from .rebuild_state import build_state
from .rebuild_state import rebuild_state
from .reporting import build_report_payload, render_report_text
from .reset_runtime import reset_alpha


SHOWCASE_STORIES: dict[str, dict[str, Any]] = {
    "local-ext": {
        "title": "Contain a local package in QTF, then promote it explicitly through EXT",
        "phase_one": {
            "label": "Phase 1: QTF containment succeeded, but EXT has not been requested yet",
            "scenario": PACKAGE_SCENARIOS_DIR / "01-local-qtf-allow.json",
            "include": ("package", "qtf"),
        },
        "phase_two": {
            "label": "Phase 2: EXT promotion is requested, so the clean local package can leave containment",
            "scenario": EXT_SCENARIOS_DIR / "01-local-ext-allow.json",
            "include": ("ext",),
        },
        "takeaways": [
            "QTF success did not silently imply host promotion.",
            "The package stayed in review until an explicit EXT request was recorded.",
            "Once EXT matched the clean QTF evidence, policy moved from review to allow.",
        ],
    },
    "registry-review": {
        "title": "Show that even an EXT request does not auto-promote a registry package",
        "phase_one": {
            "label": "Phase 1: Registry package runs cleanly in QTF, but policy still holds it in review",
            "scenario": PACKAGE_SCENARIOS_DIR / "02-registry-review.json",
            "include": ("package", "qtf"),
        },
        "phase_two": {
            "label": "Phase 2: EXT is requested, but the registry source still keeps policy at review",
            "scenario": EXT_SCENARIOS_DIR / "02-registry-ext-review.json",
            "include": ("ext",),
        },
        "takeaways": [
            "Containment success and promotion permission are different decisions.",
            "EXT made the request explicit, but the package source still mattered.",
            "This is the trust-versus-policy split in action.",
        ],
    },
    "lockdown-deny": {
        "title": "Show that a suspicious host session can deny promotion at the EXT boundary",
        "phase_one": {
            "label": "Phase 1: The package is contained cleanly, but the host session is already marked suspicious",
            "scenario": EXT_SCENARIOS_DIR / "04-lockdown-ext-deny.json",
            "include": ("host_session", "package", "qtf"),
        },
        "phase_two": {
            "label": "Phase 2: EXT is requested, and the lockdown-ready host session denies it",
            "scenario": EXT_SCENARIOS_DIR / "04-lockdown-ext-deny.json",
            "include": ("ext",),
        },
        "takeaways": [
            "Host-session suspicion remained visible all the way to the promotion boundary.",
            "EXT turned that suspicion into a real decision point instead of background telemetry.",
            "The same contained package story ended differently because the surrounding context changed.",
        ],
    },
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_package_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_package_install_event(
        manager=config.get("manager", "npm"),
        operation=config.get("operation", "install"),
        package_name=config.get("package_name", ""),
        version_spec=config.get("version_spec", ""),
        source_kind=config.get("source_kind", "local"),
        workspace_seed=config.get("workspace_seed", ""),
        command=list(config.get("command", [])),
        scripts_policy=config.get("scripts_policy", "default"),
        lockfile_state=config.get("lockfile_state", "unknown"),
        qtf_requested=bool(config.get("qtf_requested", False)),
        qtf_label=config.get("qtf_label", ""),
        qtf_backend_preference=config.get("qtf_backend_preference", "auto"),
        qtf_image=config.get("qtf_image", ""),
    )


def _build_qtf_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    execution = {
        "label": config.get("label", "local-offline-cage"),
        "backend_requested": config.get("backend_requested", "auto"),
        "backend": config.get("backend", "podman"),
        "backend_note": config.get("backend_note", "showcase"),
        "image": config.get("image", "ubuntu:latest"),
        "command": list(config.get("command", ["/bin/sh", "-lc", "true"])),
        "command_text": config.get("command_text", "/bin/sh -lc true"),
        "workspace_seed": config.get("workspace_seed", "/tmp/example"),
        "workspace_mode": config.get("workspace_mode", "directory"),
        "sandbox_kept": bool(config.get("sandbox_kept", False)),
        "sandbox_root": config.get("sandbox_root", ""),
        "manifest": dict(
            config.get(
                "manifest",
                {
                    "network": "disabled",
                    "fake_home": "/home/qtf",
                    "workspace_mount": "/workspace",
                    "read_only_system": True,
                    "tmpfs": ["/tmp", "/var/tmp", "/home/qtf"],
                },
            )
        ),
        "result": {
            "success": bool(config.get("success", True)),
            "exit_code": int(config.get("exit_code", 0)),
            "duration_ms": int(config.get("duration_ms", 1200)),
            "timed_out": bool(config.get("timed_out", False)),
        },
        "artifacts": {
            "created_files": list(config.get("created_files", [])),
            "modified_files": list(config.get("modified_files", [])),
            "deleted_files": list(config.get("deleted_files", [])),
        },
        "stdout": config.get("stdout", ""),
        "stderr": config.get("stderr", ""),
        "capture_ts": config.get("capture_ts", ""),
    }
    return build_qtf_event(execution)


def _build_ext_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_ext_event(
        result=config.get("result", "requested"),
        target=config.get("target", "host"),
        artifact_kind=config.get("artifact_kind", "package"),
        qtf_label=config.get("qtf_label", ""),
        package_name=config.get("package_name", ""),
        package_manager=config.get("package_manager", ""),
        reason=config.get("reason", ""),
    )


def _build_host_session_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_host_session_event(
        stage=config.get("stage", "gnome-handoff"),
        compromise_suspected=bool(config.get("compromise_suspected", False)),
        suspicion_note=config.get("suspicion_note", ""),
        recovery_hint=config.get("recovery_hint", "observe_only"),
    )


def _append_phase_events(config: dict[str, Any], include: tuple[str, ...]) -> None:
    if "host_session" in include and config.get("host_session"):
        append_event(_build_host_session_event_from_config(config["host_session"]))
    if "package" in include and config.get("package"):
        append_event(_build_package_event_from_config(config["package"]))
    if "qtf" in include and config.get("qtf"):
        append_event(_build_qtf_event_from_config(config["qtf"]))
    if "ext" in include and config.get("ext"):
        append_event(_build_ext_event_from_config(config["ext"]))


def _capture_report() -> dict[str, Any]:
    state = rebuild_state()
    tags = project_tags()
    busydawg = project_busydawg()
    report = build_report_payload(state, tags, busydawg)
    return {
        "state": state,
        "tags": tags,
        "busydawg": busydawg,
        "report": report,
        "report_text": render_report_text(report),
    }


def _append_phase_events_in_memory(
    events: list[dict[str, Any]],
    config: dict[str, Any],
    include: tuple[str, ...],
) -> None:
    if "host_session" in include and config.get("host_session"):
        events.append(normalize_event(_build_host_session_event_from_config(config["host_session"])))
    if "package" in include and config.get("package"):
        events.append(normalize_event(_build_package_event_from_config(config["package"])))
    if "qtf" in include and config.get("qtf"):
        events.append(normalize_event(_build_qtf_event_from_config(config["qtf"])))
    if "ext" in include and config.get("ext"):
        events.append(normalize_event(_build_ext_event_from_config(config["ext"])))


def _capture_report_in_memory(events: list[dict[str, Any]]) -> dict[str, Any]:
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)
    return {
        "state": state,
        "tags": tags,
        "busydawg": busydawg,
        "report": report,
        "report_text": render_report_text(report),
    }


def build_showcase_story(story: str = "local-ext") -> dict[str, Any]:
    if story not in SHOWCASE_STORIES:
        raise ValueError(f"Unknown showcase story: {story}")

    definition = SHOWCASE_STORIES[story]
    events: list[dict[str, Any]] = []

    phase_one_config = _load_json(definition["phase_one"]["scenario"])
    _append_phase_events_in_memory(events, phase_one_config, tuple(definition["phase_one"]["include"]))
    phase_one_snapshot = _capture_report_in_memory(list(events))

    phase_two_config = _load_json(definition["phase_two"]["scenario"])
    _append_phase_events_in_memory(events, phase_two_config, tuple(definition["phase_two"]["include"]))
    phase_two_snapshot = _capture_report_in_memory(list(events))

    return {
        "status": "showcased",
        "story": story,
        "title": definition["title"],
        "phases": [
            {
                "name": "phase_one",
                "label": definition["phase_one"]["label"],
                **phase_one_snapshot,
            },
            {
                "name": "phase_two",
                "label": definition["phase_two"]["label"],
                **phase_two_snapshot,
            },
        ],
        "takeaways": list(definition.get("takeaways", [])),
    }


def build_showcase_catalog() -> dict[str, Any]:
    stories = [build_showcase_story(story) for story in ("local-ext", "registry-review", "lockdown-deny")]
    return {
        "status": "ok",
        "count": len(stories),
        "stories": stories,
    }


def run_showcase_demo(*, story: str = "local-ext", archive: bool = False) -> dict[str, Any]:
    definition = SHOWCASE_STORIES[story]
    reset_result = reset_alpha(archive=archive)

    phase_one_config = _load_json(definition["phase_one"]["scenario"])
    _append_phase_events(phase_one_config, tuple(definition["phase_one"]["include"]))
    phase_one_snapshot = _capture_report()

    phase_two_config = _load_json(definition["phase_two"]["scenario"])
    _append_phase_events(phase_two_config, tuple(definition["phase_two"]["include"]))
    phase_two_snapshot = _capture_report()

    return {
        "status": "showcased",
        "story": story,
        "title": definition["title"],
        "reset": reset_result,
        "phases": [
            {
                "name": "phase_one",
                "label": definition["phase_one"]["label"],
                **phase_one_snapshot,
            },
            {
                "name": "phase_two",
                "label": definition["phase_two"]["label"],
                **phase_two_snapshot,
            },
        ],
        "takeaways": list(definition.get("takeaways", [])),
    }


def render_showcase_text(showcase: dict[str, Any]) -> str:
    lines = [
        "QTMoS Alpha Showcase",
        f"Story: {showcase.get('title', showcase.get('story', 'unknown'))}",
        "",
    ]

    for phase in showcase.get("phases", []):
        lines.append(phase.get("label", phase.get("name", "phase")))
        lines.append("-" * len(lines[-1]))
        lines.append(phase.get("report_text", "").rstrip())
        lines.append("")

    takeaways = showcase.get("takeaways") or []
    if takeaways:
        lines.append("What This Shows")
        lines.append("----------------")
        for item in takeaways:
            lines.append(f"- {item}")

    return "\n".join(lines).rstrip() + "\n"
