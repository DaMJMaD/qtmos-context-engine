from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import dump_json
from .paths import BUSYDAWG_STATE_JSON, LATEST_STATE_JSON, LATEST_TAGS_JSON


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_report_payload(
    state: dict[str, Any],
    tags: dict[str, Any],
    busydawg: dict[str, Any],
) -> dict[str, Any]:
    active_surface = state.get("active_surface") or {}
    active_web = state.get("active_web") or {}
    active_mindseye = state.get("active_mindseye") or {}
    active_ahk_feedback = state.get("active_ahk_feedback") or {}
    active_qtf_execution = state.get("active_qtf_execution") or {}
    active_package_install = state.get("active_package_install") or {}
    active_host_session = state.get("active_host_session") or {}
    active_privilege = state.get("active_privilege") or {}
    active_ext_promotion = state.get("active_ext_promotion") or {}
    binding = tags.get("binding_evidence") or {}
    policy = busydawg.get("policy") or {}

    return {
        "report_version": "alpha-v1",
        "overall_status": tags.get("trust_status", "unknown"),
        "summary": tags.get("summary", "unknown: insufficient evidence"),
        "active_surface": {
            "title": tags.get("active_surface_title"),
            "surface_id": tags.get("active_surface_id"),
            "process_name": active_surface.get("process_name"),
            "process_path": active_surface.get("process_path"),
            "surface_trust": active_surface.get("trust_status", "unknown"),
        },
        "active_web": {
            "title": tags.get("active_web_title"),
            "origin": tags.get("active_web_origin"),
            "web_trust": binding.get("web_trust_status", active_web.get("trust_status", "unknown")),
        },
        "binding": {
            "linked_surface_id": binding.get("linked_surface_id"),
            "linked_surface_title": binding.get("linked_surface_title"),
            "link_confidence": binding.get("link_confidence", "none"),
            "binding_used_in_trust": bool(binding.get("binding_used_in_trust", False)),
            "match_signals": binding.get("match_signals", []),
            "mismatch_signals": binding.get("mismatch_signals", []),
            "trust_reasons": binding.get("trust_reasons", []),
        },
        "active_mindseye": {
            "channel": active_mindseye.get("channel"),
            "stage": active_mindseye.get("stage"),
            "condition": active_mindseye.get("condition"),
            "context_summary": active_mindseye.get("context_summary"),
            "focus_level": active_mindseye.get("focus_level"),
            "stress_level": active_mindseye.get("stress_level"),
            "intent_signal": active_mindseye.get("intent_signal"),
            "raw_text": active_mindseye.get("raw_text"),
            "observer": active_mindseye.get("observer"),
            "binding": active_mindseye.get("binding", {}),
        },
        "active_ahk_feedback": {
            "user_response": active_ahk_feedback.get("user_response"),
            "original_action": active_ahk_feedback.get("original_action"),
            "original_rule": active_ahk_feedback.get("original_rule"),
            "surface_id": active_ahk_feedback.get("surface_id"),
            "surface_title": active_ahk_feedback.get("surface_title"),
            "web_origin": active_ahk_feedback.get("web_origin"),
            "reason": active_ahk_feedback.get("reason"),
            "capture_ts": active_ahk_feedback.get("capture_ts"),
        },
        "active_qtf_execution": {
            "label": active_qtf_execution.get("label"),
            "backend_requested": active_qtf_execution.get("backend_requested"),
            "backend": active_qtf_execution.get("backend"),
            "backend_note": active_qtf_execution.get("backend_note"),
            "image": active_qtf_execution.get("image"),
            "command_text": active_qtf_execution.get("command_text"),
            "workspace_seed": active_qtf_execution.get("workspace_seed"),
            "workspace_mode": active_qtf_execution.get("workspace_mode"),
            "success": active_qtf_execution.get("success"),
            "exit_code": active_qtf_execution.get("exit_code"),
            "duration_ms": active_qtf_execution.get("duration_ms"),
            "timed_out": active_qtf_execution.get("timed_out"),
            "created_files": active_qtf_execution.get("created_files", []),
            "modified_files": active_qtf_execution.get("modified_files", []),
            "deleted_files": active_qtf_execution.get("deleted_files", []),
        },
        "active_package_install": {
            "manager": active_package_install.get("manager"),
            "operation": active_package_install.get("operation"),
            "package_name": active_package_install.get("package_name"),
            "version_spec": active_package_install.get("version_spec"),
            "source_kind": active_package_install.get("source_kind"),
            "workspace_seed": active_package_install.get("workspace_seed"),
            "command_text": active_package_install.get("command_text"),
            "scripts_policy": active_package_install.get("scripts_policy"),
            "lockfile_state": active_package_install.get("lockfile_state"),
            "qtf_requested": active_package_install.get("qtf_requested"),
            "qtf_label": active_package_install.get("qtf_label"),
        },
        "active_host_session": {
            "stage": active_host_session.get("stage"),
            "hostname": active_host_session.get("hostname"),
            "user": active_host_session.get("user"),
            "boot_id": active_host_session.get("boot_id"),
            "desktop_session": active_host_session.get("desktop_session"),
            "current_desktop": active_host_session.get("current_desktop"),
            "session_type": active_host_session.get("session_type"),
            "display": active_host_session.get("display"),
            "wayland_display": active_host_session.get("wayland_display"),
            "compromise_suspected": active_host_session.get("compromise_suspected"),
            "suspicion_note": active_host_session.get("suspicion_note"),
            "recovery_hint": active_host_session.get("recovery_hint"),
        },
        "active_privilege": {
            "method": active_privilege.get("method"),
            "result": active_privilege.get("result"),
            "target_user": active_privilege.get("target_user"),
            "target_uid": active_privilege.get("target_uid"),
            "command_text": active_privilege.get("command_text"),
            "reason": active_privilege.get("reason"),
            "capture_ts": active_privilege.get("capture_ts"),
        },
        "active_ext_promotion": {
            "result": active_ext_promotion.get("result"),
            "target": active_ext_promotion.get("target"),
            "artifact_kind": active_ext_promotion.get("artifact_kind"),
            "qtf_label": active_ext_promotion.get("qtf_label"),
            "package_name": active_ext_promotion.get("package_name"),
            "package_manager": active_ext_promotion.get("package_manager"),
            "reason": active_ext_promotion.get("reason"),
            "capture_ts": active_ext_promotion.get("capture_ts"),
        },
        "timing": {
            "rebuilt_at": state.get("rebuilt_at"),
            "last_focus_change_ts": tags.get("last_focus_change_ts"),
            "last_web_change_ts": tags.get("last_web_change_ts"),
            "last_mindseye_change_ts": state.get("last_mindseye_change_ts"),
            "last_ahk_feedback_ts": state.get("last_ahk_feedback_ts"),
            "last_qtf_execution_ts": state.get("last_qtf_execution_ts"),
            "last_package_install_ts": state.get("last_package_install_ts"),
            "last_host_session_ts": state.get("last_host_session_ts"),
            "last_privilege_ts": state.get("last_privilege_ts"),
            "last_ext_ts": state.get("last_ext_ts"),
            "event_count": state.get("event_count", 0),
        },
        "busydawg": {
            "hot_node": busydawg.get("hot_node"),
            "rail_state": busydawg.get("rail_state"),
            "summary": busydawg.get("summary"),
        },
        "policy": {
            "action": policy.get("action", "warn"),
            "policy_rule": policy.get("policy_rule", "default_fallback"),
            "reason": policy.get("reason", ""),
            "applied_at": policy.get("applied_at"),
        },
        "paths": {
            "state": str(LATEST_STATE_JSON),
            "tags": str(LATEST_TAGS_JSON),
            "busydawg": str(BUSYDAWG_STATE_JSON),
        },
    }


def load_report_payload() -> dict[str, Any]:
    return build_report_payload(
        _load_json(LATEST_STATE_JSON),
        _load_json(LATEST_TAGS_JSON),
        _load_json(BUSYDAWG_STATE_JSON),
    )


def render_report_text(report: dict[str, Any]) -> str:
    surface = report.get("active_surface", {})
    web = report.get("active_web", {})
    binding = report.get("binding", {})
    mindseye = report.get("active_mindseye", {})
    feedback = report.get("active_ahk_feedback", {})
    qtf = report.get("active_qtf_execution", {})
    package = report.get("active_package_install", {})
    host_session = report.get("active_host_session", {})
    privilege = report.get("active_privilege", {})
    ext = report.get("active_ext_promotion", {})
    timing = report.get("timing", {})
    policy = report.get("policy", {})

    lines = [
        "QTMoS Alpha Report",
        f"Overall trust: {report.get('overall_status', 'unknown')}",
        f"Summary: {report.get('summary', '')}",
        f"Policy: {policy.get('action', 'warn')} ({policy.get('policy_rule', 'default_fallback')})",
        f"Policy reason: {policy.get('reason', '') or 'n/a'}",
        f"Surface: {surface.get('title') or 'none'}",
        f"Web: {web.get('title') or 'none'}",
        f"Origin: {web.get('origin') or 'none'}",
        f"Web trust: {web.get('web_trust', 'unknown')}",
        (
            "AHK context: "
            f"{mindseye.get('context_summary') or mindseye.get('condition') or mindseye.get('raw_text') or 'none'}"
        ),
        (
            "AHK context binding: "
            f"{(mindseye.get('binding') or {}).get('confidence', 'none')} -> "
            f"{(mindseye.get('binding') or {}).get('linked_surface_title') or 'unbound'}"
        ),
        (
            "AHK feedback: "
            f"{feedback.get('user_response') or 'none'}"
            + (
                f" ({feedback.get('original_action')})"
                if feedback.get("original_action")
                else ""
            )
        ),
        (
            "Host session: "
            + (
                f"{host_session.get('stage') or 'none'}"
                + (
                    f" on {host_session.get('current_desktop') or host_session.get('desktop_session') or 'unknown-desktop'}"
                    if host_session
                    else ""
                )
            )
        ),
        (
            "Privilege: "
            + (
                f"{privilege.get('method') or 'none'}"
                + (f" {privilege.get('result')}" if privilege and privilege.get("result") else "")
                + (
                    f" -> {privilege.get('command_text')}"
                    if privilege and privilege.get("command_text")
                    else ""
                )
            )
        ),
        (
            "Package: "
            f"{(package.get('manager') or 'none')}"
            + (
                f" {package.get('operation') or ''} {package.get('package_name') or ''}".rstrip()
                if package
                else ""
            )
        ),
        (
            "QTF: "
            f"{('success' if qtf.get('success') else 'failed') if qtf else 'none'}"
            + (
                f" via {qtf.get('backend')} ({qtf.get('label')})"
                if qtf
                else ""
            )
        ),
        (
            "EXT: "
            + (
                f"{ext.get('result') or 'none'}"
                + (f" -> {ext.get('target')}" if ext and ext.get("target") else "")
                + (
                    f" ({ext.get('qtf_label') or ext.get('package_name')})"
                    if ext and (ext.get("qtf_label") or ext.get("package_name"))
                    else ""
                )
            )
        ),
        (
            "Binding: "
            f"{binding.get('link_confidence', 'none')} -> "
            f"{binding.get('linked_surface_title') or binding.get('linked_surface_id') or 'unbound'}"
        ),
        f"Binding used in trust: {'yes' if binding.get('binding_used_in_trust') else 'no'}",
        f"Events: {timing.get('event_count', 0)}",
        f"Last update: {timing.get('rebuilt_at') or 'n/a'}",
    ]

    reasons = binding.get("trust_reasons") or []
    if reasons:
        lines.append("Reasons: " + ", ".join(reasons[:3]))
    match_signals = binding.get("match_signals") or []
    if match_signals:
        lines.append("Match signals: " + ", ".join(match_signals[:3]))
    mismatch_signals = binding.get("mismatch_signals") or []
    if mismatch_signals:
        lines.append("Mismatch signals: " + ", ".join(mismatch_signals[:3]))
    if feedback.get("reason"):
        lines.append("Feedback reason: " + str(feedback.get("reason")))
    if host_session:
        boot_short = str(host_session.get("boot_id") or "")[:8] or "n/a"
        lines.append(
            "Host breadcrumb: "
            f"{host_session.get('hostname') or 'unknown'} "
            f"{host_session.get('session_type') or 'unknown'} "
            f"boot:{boot_short}"
        )
        lines.append(
            "Recovery hint: "
            f"{host_session.get('recovery_hint') or 'observe_only'}"
            + (" [suspected]" if host_session.get("compromise_suspected") else "")
        )
        if host_session.get("suspicion_note"):
            lines.append("Suspicion note: " + str(host_session.get("suspicion_note")))
    if privilege.get("target_user"):
        lines.append("Privilege target: " + str(privilege.get("target_user")))
    if privilege.get("reason"):
        lines.append("Privilege reason: " + str(privilege.get("reason")))
    if ext.get("reason"):
        lines.append("EXT reason: " + str(ext.get("reason")))
    if package:
        lines.append(
            "Package route: "
            + (
                f"qtf:{package.get('qtf_label')}"
                if package.get("qtf_requested")
                else "host-observe-only"
            )
        )
    if qtf:
        lines.append(f"QTF command: {qtf.get('command_text') or 'n/a'}")
        lines.append(
            "QTF changes: "
            f"+{len(qtf.get('created_files', []))} "
            f"~{len(qtf.get('modified_files', []))} "
            f"-{len(qtf.get('deleted_files', []))}"
        )
    return "\n".join(lines)


def dump_report_json(report: dict[str, Any]) -> str:
    return dump_json(report)
