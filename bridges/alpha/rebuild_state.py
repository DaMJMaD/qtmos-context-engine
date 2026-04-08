from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .appender import load_events
from .mindseye import _context_summary, _normalize_context_observer, _normalize_context_subject, build_mindseye_binding
from .models import dump_json
from .paths import EVENTS_JSONL, LATEST_STATE_JSON, ensure_runtime_dirs


def _surface_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("surface_observation", {})
    trust = payload.get("trust_state", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "surface_id": observation.get("surface_id") or observation.get("hwnd") or observation.get("x11_id"),
        "platform": observation.get("platform"),
        "process_name": observation.get("process_name"),
        "process_path": observation.get("process_path"),
        "window_class": observation.get("window_class"),
        "window_title": observation.get("window_title"),
        "bounds": observation.get("bounds", {}),
        "focused": observation.get("focused"),
        "trust_status": trust.get("status", "unknown"),
        "drift_flags": trust.get("drift_flags", []),
        "mismatch_flags": trust.get("mismatch_flags", []),
        "signature": payload.get("surface_signature", {}),
    }


def _record_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "kind": payload.get("kind"),
        "subject": payload.get("subject"),
        "value": payload.get("value"),
        "text": payload.get("text"),
    }


def _web_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("web_observation", {})
    trust = payload.get("trust_state", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "browser": observation.get("browser"),
        "url": observation.get("url"),
        "origin": observation.get("origin"),
        "domain": observation.get("domain"),
        "title": observation.get("title"),
        "text_snippet": observation.get("text_snippet"),
        "tab_id": observation.get("tab_id"),
        "window_id": observation.get("window_id"),
        "mutated": observation.get("mutated"),
        "visible": observation.get("visible"),
        "linked_surface": observation.get("linked_surface", {}),
        "link_confidence": observation.get("linked_surface", {}).get("link_confidence", "none"),
        "trust_status": trust.get("status", "unknown"),
        "drift_flags": trust.get("drift_flags", []),
        "mismatch_flags": trust.get("mismatch_flags", []),
        "trust_reasons": trust.get("trust_reasons", []),
        "binding_used_in_trust": bool(trust.get("binding_used_in_trust", False)),
        "trust_summary": trust.get("summary", ""),
        "signature": payload.get("web_signature", {}),
    }


def _mindseye_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("mindseye_observation", {})
    normalized_observer = _normalize_context_observer(
        event.get("source", {}).get("observer") or observation.get("observer")
    )
    normalized_subject = _normalize_context_subject(observation.get("subject"))
    context_summary = observation.get("context_summary") or _context_summary(observation)
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": normalized_observer,
        "channel": observation.get("channel"),
        "source_name": observation.get("source"),
        "subject": normalized_subject,
        "capture_ts": observation.get("capture_ts"),
        "stage": observation.get("stage"),
        "raw_text": observation.get("raw_text"),
        "context_summary": context_summary,
        "condition": observation.get("condition"),
        "focus_level": observation.get("focus_level"),
        "stress_level": observation.get("stress_level"),
        "intent_signal": observation.get("intent_signal"),
        "shared_root": observation.get("shared_root"),
        "shared_channel_dir": observation.get("shared_channel_dir"),
        "signature": payload.get("mindseye_signature", {}),
    }


def _ahk_feedback_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("feedback_observation", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "channel": observation.get("channel"),
        "source_name": observation.get("source"),
        "subject": observation.get("subject"),
        "capture_ts": observation.get("capture_ts"),
        "original_hook_id": observation.get("original_hook_id"),
        "original_action": observation.get("original_action"),
        "original_rule": observation.get("original_rule"),
        "user_response": observation.get("user_response"),
        "surface_id": observation.get("surface_id"),
        "surface_title": observation.get("surface_title"),
        "web_origin": observation.get("web_origin"),
        "reason": observation.get("reason"),
        "context_condition": observation.get("context_condition"),
        "summary": observation.get("summary"),
        "shared_root": observation.get("shared_root"),
        "shared_channel_dir": observation.get("shared_channel_dir"),
        "signature": payload.get("feedback_signature", {}),
    }


def _qtf_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    execution = payload.get("qtf_execution", {})
    result = execution.get("result", {})
    artifacts = execution.get("artifacts", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "label": execution.get("label"),
        "backend_requested": execution.get("backend_requested"),
        "backend": execution.get("backend"),
        "backend_note": execution.get("backend_note"),
        "image": execution.get("image"),
        "command": execution.get("command", []),
        "command_text": execution.get("command_text"),
        "workspace_seed": execution.get("workspace_seed"),
        "workspace_mode": execution.get("workspace_mode"),
        "sandbox_kept": execution.get("sandbox_kept"),
        "sandbox_root": execution.get("sandbox_root"),
        "success": bool(result.get("success", False)),
        "exit_code": result.get("exit_code"),
        "duration_ms": result.get("duration_ms"),
        "timed_out": bool(result.get("timed_out", False)),
        "stdout": execution.get("stdout", ""),
        "stderr": execution.get("stderr", ""),
        "created_files": artifacts.get("created_files", []),
        "modified_files": artifacts.get("modified_files", []),
        "deleted_files": artifacts.get("deleted_files", []),
        "manifest": execution.get("manifest", {}),
        "signature": payload.get("qtf_signature", {}),
    }


def _package_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("package_observation", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "manager": observation.get("manager"),
        "operation": observation.get("operation"),
        "package_name": observation.get("package_name"),
        "version_spec": observation.get("version_spec"),
        "source_kind": observation.get("source_kind"),
        "workspace_seed": observation.get("workspace_seed"),
        "command": observation.get("command", []),
        "command_text": observation.get("command_text"),
        "scripts_policy": observation.get("scripts_policy"),
        "lockfile_state": observation.get("lockfile_state"),
        "qtf_requested": bool(observation.get("qtf_requested", False)),
        "qtf_label": observation.get("qtf_label"),
        "qtf_backend_preference": observation.get("qtf_backend_preference"),
        "qtf_image": observation.get("qtf_image"),
        "signature": payload.get("package_signature", {}),
    }


def _host_session_summary(event: dict[str, Any]) -> dict[str, Any]:
    payload = event.get("payload", {})
    observation = payload.get("host_session_observation", {})
    return {
        "event_id": event.get("id"),
        "ts": event.get("ts"),
        "observer": event.get("source", {}).get("observer", event.get("source", {}).get("host", "unknown")),
        "stage": observation.get("stage"),
        "capture_ts": observation.get("capture_ts"),
        "hostname": observation.get("hostname"),
        "user": observation.get("user"),
        "uid": observation.get("uid"),
        "shell": observation.get("shell"),
        "home": observation.get("home"),
        "cwd": observation.get("cwd"),
        "platform": observation.get("platform"),
        "desktop_session": observation.get("desktop_session"),
        "current_desktop": observation.get("current_desktop"),
        "session_type": observation.get("session_type"),
        "session_id": observation.get("session_id"),
        "display": observation.get("display"),
        "wayland_display": observation.get("wayland_display"),
        "tty": observation.get("tty"),
        "boot_id": observation.get("boot_id"),
        "machine_id_present": observation.get("machine_id_present"),
        "compromise_suspected": bool(observation.get("compromise_suspected", False)),
        "suspicion_note": observation.get("suspicion_note", ""),
        "recovery_hint": observation.get("recovery_hint", "observe_only"),
        "signature": payload.get("host_session_signature", {}),
    }


def build_state(events: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter()
    host_counts = Counter()
    active_surface: dict[str, Any] | None = None
    previous_active_surface: dict[str, Any] | None = None
    last_focus_change_ts: str | None = None
    active_web: dict[str, Any] | None = None
    previous_active_web: dict[str, Any] | None = None
    last_web_change_ts: str | None = None
    active_mindseye: dict[str, Any] | None = None
    previous_active_mindseye: dict[str, Any] | None = None
    last_mindseye_change_ts: str | None = None
    active_ahk_feedback: dict[str, Any] | None = None
    previous_active_ahk_feedback: dict[str, Any] | None = None
    last_ahk_feedback_ts: str | None = None
    active_qtf_execution: dict[str, Any] | None = None
    previous_active_qtf_execution: dict[str, Any] | None = None
    last_qtf_execution_ts: str | None = None
    active_package_install: dict[str, Any] | None = None
    previous_active_package_install: dict[str, Any] | None = None
    last_package_install_ts: str | None = None
    active_host_session: dict[str, Any] | None = None
    previous_active_host_session: dict[str, Any] | None = None
    last_host_session_ts: str | None = None
    recent_events: list[dict[str, Any]] = []
    learned: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    observer_surfaces: dict[str, dict[str, Any]] = {}
    observer_web: dict[str, dict[str, Any]] = {}
    observer_mindseye: dict[str, dict[str, Any]] = {}
    observer_ahk_feedback: dict[str, dict[str, Any]] = {}
    observer_qtf: dict[str, dict[str, Any]] = {}
    observer_package: dict[str, dict[str, Any]] = {}
    observer_host_session: dict[str, dict[str, Any]] = {}
    last_surface_web_binding: dict[str, Any] | None = None
    subjects: dict[str, Any] = {}

    for event in events:
        event_type = event.get("type", "unknown")
        counts[event_type] += 1
        host_counts[event.get("source", {}).get("host", "unknown")] += 1
        recent_events.append(
            {
                "id": event.get("id"),
                "ts": event.get("ts"),
                "type": event_type,
                "host": event.get("source", {}).get("host", "unknown"),
            }
        )
        recent_events = recent_events[-12:]

        if event_type == "surface.observe":
            summary = _surface_summary(event)
            if active_surface and summary.get("surface_id") != active_surface.get("surface_id"):
                previous_active_surface = active_surface
                last_focus_change_ts = summary.get("ts")
            active_surface = summary
            observer_surfaces[summary["observer"]] = summary
            if summary.get("surface_id"):
                subjects[f"surface:{summary['surface_id']}"] = summary
        elif event_type == "web.observe":
            summary = _web_summary(event)
            if active_web and (
                summary.get("tab_id") != active_web.get("tab_id")
                or summary.get("origin") != active_web.get("origin")
                or summary.get("title") != active_web.get("title")
            ):
                previous_active_web = active_web
                last_web_change_ts = summary.get("ts")
            active_web = summary
            observer_web[summary["observer"]] = summary
            binding = summary.get("linked_surface", {})
            if binding.get("surface_id") and binding.get("link_confidence") not in {"", "none"}:
                last_surface_web_binding = {
                    "event_id": summary.get("event_id"),
                    "ts": summary.get("ts"),
                    "surface_id": binding.get("surface_id"),
                    "window_title": binding.get("window_title"),
                    "process_name": binding.get("process_name"),
                    "process_path": binding.get("process_path"),
                    "link_confidence": binding.get("link_confidence"),
                    "match_signals": binding.get("match_signals", []),
                    "mismatch_signals": binding.get("mismatch_signals", []),
                    "web_origin": summary.get("origin"),
                    "web_title": summary.get("title"),
                    "binding_used_in_trust": summary.get("binding_used_in_trust", False),
                    "trust_reasons": summary.get("trust_reasons", []),
                }
            if summary.get("tab_id"):
                subjects[f"web:tab:{summary['tab_id']}"] = summary
        elif event_type == "mindseye.vitals":
            summary = _mindseye_summary(event)
            if active_mindseye and (
                summary.get("raw_text") != active_mindseye.get("raw_text")
                or summary.get("condition") != active_mindseye.get("condition")
                or summary.get("stage") != active_mindseye.get("stage")
            ):
                previous_active_mindseye = active_mindseye
                last_mindseye_change_ts = summary.get("ts")
            active_mindseye = summary
            observer_mindseye[summary["observer"]] = summary
            if summary.get("channel"):
                subjects[f"mindseye:{summary['channel']}"] = summary
        elif event_type == "ahk.feedback":
            summary = _ahk_feedback_summary(event)
            if active_ahk_feedback and (
                summary.get("user_response") != active_ahk_feedback.get("user_response")
                or summary.get("original_hook_id") != active_ahk_feedback.get("original_hook_id")
                or summary.get("original_rule") != active_ahk_feedback.get("original_rule")
            ):
                previous_active_ahk_feedback = active_ahk_feedback
                last_ahk_feedback_ts = summary.get("ts")
            active_ahk_feedback = summary
            observer_ahk_feedback[summary["observer"]] = summary
            if summary.get("channel"):
                subjects[f"ahk_feedback:{summary['channel']}"] = summary
        elif event_type == "qtf.execution":
            summary = _qtf_summary(event)
            if active_qtf_execution and (
                summary.get("label") != active_qtf_execution.get("label")
                or summary.get("command_text") != active_qtf_execution.get("command_text")
                or summary.get("success") != active_qtf_execution.get("success")
                or summary.get("ts") != active_qtf_execution.get("ts")
            ):
                previous_active_qtf_execution = active_qtf_execution
                last_qtf_execution_ts = summary.get("ts")
            active_qtf_execution = summary
            observer_qtf[summary["observer"]] = summary
            if summary.get("label"):
                subjects[f"qtf:{summary['label']}"] = summary
        elif event_type == "package.install.observe":
            summary = _package_summary(event)
            if active_package_install and (
                summary.get("manager") != active_package_install.get("manager")
                or summary.get("command_text") != active_package_install.get("command_text")
                or summary.get("ts") != active_package_install.get("ts")
            ):
                previous_active_package_install = active_package_install
                last_package_install_ts = summary.get("ts")
            active_package_install = summary
            observer_package[summary["observer"]] = summary
            subject_key = summary.get("package_name") or summary.get("manager") or "package"
            subjects[f"package:{subject_key}"] = summary
        elif event_type == "host.session.observe":
            summary = _host_session_summary(event)
            if active_host_session and (
                summary.get("stage") != active_host_session.get("stage")
                or summary.get("boot_id") != active_host_session.get("boot_id")
                or summary.get("compromise_suspected") != active_host_session.get("compromise_suspected")
                or summary.get("ts") != active_host_session.get("ts")
            ):
                previous_active_host_session = active_host_session
                last_host_session_ts = summary.get("ts")
            active_host_session = summary
            observer_host_session[summary["observer"]] = summary
            subjects[f"host_session:{summary.get('stage') or 'session'}"] = summary
        elif event_type in {"memory.note", "bridge.learn"}:
            summary = _record_summary(event)
            learned.append(summary)
            learned = learned[-25:]
        elif event_type in {"session.record", "bridge.record", "host.capture"}:
            summary = _record_summary(event)
            records.append(summary)
            records = records[-50:]
            subject = summary.get("subject")
            if subject:
                subjects[f"subject:{subject}"] = summary
        elif event_type == "state.set":
            payload = event.get("payload", {})
            subject = payload.get("subject")
            if subject:
                subjects[f"state:{subject}"] = {
                    "event_id": event.get("id"),
                    "ts": event.get("ts"),
                    "subject": subject,
                    "value": payload.get("value"),
                }

    if active_mindseye:
        active_mindseye = {
            **active_mindseye,
            "binding": build_mindseye_binding(active_mindseye, active_surface, active_web),
        }

    return {
        "status": "operational",
        "rebuilt_at": recent_events[-1]["ts"] if recent_events else None,
        "event_count": len(events),
        "event_types": dict(counts),
        "host_counts": dict(host_counts),
        "active_surface": active_surface,
        "previous_active_surface": previous_active_surface,
        "last_focus_change_ts": last_focus_change_ts,
        "active_web": active_web,
        "previous_active_web": previous_active_web,
        "last_web_change_ts": last_web_change_ts,
        "active_mindseye": active_mindseye,
        "previous_active_mindseye": previous_active_mindseye,
        "last_mindseye_change_ts": last_mindseye_change_ts,
        "active_ahk_feedback": active_ahk_feedback,
        "previous_active_ahk_feedback": previous_active_ahk_feedback,
        "last_ahk_feedback_ts": last_ahk_feedback_ts,
        "active_qtf_execution": active_qtf_execution,
        "previous_active_qtf_execution": previous_active_qtf_execution,
        "last_qtf_execution_ts": last_qtf_execution_ts,
        "active_package_install": active_package_install,
        "previous_active_package_install": previous_active_package_install,
        "last_package_install_ts": last_package_install_ts,
        "active_host_session": active_host_session,
        "previous_active_host_session": previous_active_host_session,
        "last_host_session_ts": last_host_session_ts,
        "surface_by_observer": observer_surfaces,
        "web_by_observer": observer_web,
        "mindseye_by_observer": observer_mindseye,
        "ahk_feedback_by_observer": observer_ahk_feedback,
        "qtf_by_observer": observer_qtf,
        "package_by_observer": observer_package,
        "host_session_by_observer": observer_host_session,
        "last_surface_web_binding": last_surface_web_binding,
        "recent_events": recent_events,
        "learned": learned,
        "records": records,
        "subjects": subjects,
    }


def rebuild_state(event_path: Path = EVENTS_JSONL, output_path: Path = LATEST_STATE_JSON) -> dict[str, Any]:
    ensure_runtime_dirs()
    state = build_state(load_events(event_path))
    output_path.write_text(dump_json(state) + "\n", encoding="utf-8")
    return state
