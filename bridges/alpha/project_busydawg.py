from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import dump_json
from .policy import decide_policy
from .paths import BUSYDAWG_STATE_JSON, LATEST_STATE_JSON, LATEST_TAGS_JSON, ensure_runtime_dirs


def build_busydawg_projection(state: dict[str, Any], tags: dict[str, Any]) -> dict[str, Any]:
    active_surface = state.get("active_surface") or {}
    active_web = state.get("active_web") or {}
    active_mindseye = state.get("active_mindseye") or {}
    active_ahk_feedback = state.get("active_ahk_feedback") or {}
    active_qtf_execution = state.get("active_qtf_execution") or {}
    active_package_install = state.get("active_package_install") or {}
    active_host_session = state.get("active_host_session") or {}
    mindseye_binding = active_mindseye.get("binding") or {}
    binding = active_web.get("linked_surface") or {}
    trust_status = tags.get("trust_status", "unknown")
    rail_state = tags.get("rails", {}).get("pm_rail", {}).get("fused_state", "unknown")
    event_count = state.get("event_count", 0)
    binding_reason = (active_web.get("trust_reasons") or [None])[0]
    policy = decide_policy(state, tags)
    policy_action = policy.get("action", "warn")
    policy_reason = policy.get("reason", "")

    nodes = [
        {
            "id": "bd_root",
            "label": "QTMoS Root",
            "kind": "root",
            "rail": rail_state,
            "active": True,
        },
        {
            "id": "bd_surface_active",
            "label": active_surface.get("window_title") or "No Active Surface",
            "kind": "surface",
            "rail": trust_status,
            "active": bool(active_surface),
            "meta": {
                "surface_id": active_surface.get("surface_id"),
                "process_name": active_surface.get("process_name"),
            },
        },
        {
            "id": "bd_events_total",
            "label": f"Events:{event_count}",
            "kind": "counter",
            "rail": "0rail",
            "active": event_count > 0,
        },
        {
            "id": "bd_policy_active",
            "label": f"Policy:{policy_action}",
            "kind": "policy",
            "rail": (
                "trusted"
                if policy_action == "allow"
                else "shifted"
                if policy_action in {"warn", "review"}
                else "suspicious"
            ),
            "active": True,
            "meta": {
                "policy_rule": policy.get("policy_rule"),
                "reason": policy_reason,
                "applied_at": policy.get("applied_at"),
            },
        },
    ]
    if active_qtf_execution:
        nodes.insert(
            1,
            {
                "id": "bd_qtf_active",
                "label": f"QTF:{'ok' if active_qtf_execution.get('success') else 'fail'}",
                "kind": "qtf",
                "rail": "trusted" if active_qtf_execution.get("success") else "shifted",
                "active": True,
                "meta": {
                    "label": active_qtf_execution.get("label"),
                    "backend": active_qtf_execution.get("backend"),
                    "exit_code": active_qtf_execution.get("exit_code"),
                    "command_text": active_qtf_execution.get("command_text"),
                    "created_files": len(active_qtf_execution.get("created_files", [])),
                    "modified_files": len(active_qtf_execution.get("modified_files", [])),
                    "deleted_files": len(active_qtf_execution.get("deleted_files", [])),
                },
            },
        )
    if active_package_install:
        nodes.insert(
            1,
            {
                "id": "bd_package_active",
                "label": (
                    f"{active_package_install.get('manager') or 'pkg'}:"
                    f"{active_package_install.get('package_name') or active_package_install.get('operation') or 'install'}"
                ),
                "kind": "package",
                "rail": "trusted" if active_package_install.get("qtf_requested") else "0rail",
                "active": True,
                "meta": {
                    "manager": active_package_install.get("manager"),
                    "operation": active_package_install.get("operation"),
                    "package_name": active_package_install.get("package_name"),
                    "source_kind": active_package_install.get("source_kind"),
                    "qtf_requested": active_package_install.get("qtf_requested"),
                    "qtf_label": active_package_install.get("qtf_label"),
                },
            },
        )
    if active_host_session:
        nodes.insert(
            1,
            {
                "id": "bd_host_session_active",
                "label": active_host_session.get("stage") or "host-session",
                "kind": "host_session",
                "rail": "shifted" if active_host_session.get("compromise_suspected") else "trusted",
                "active": True,
                "meta": {
                    "hostname": active_host_session.get("hostname"),
                    "session_type": active_host_session.get("session_type"),
                    "current_desktop": active_host_session.get("current_desktop"),
                    "boot_id": active_host_session.get("boot_id"),
                    "recovery_hint": active_host_session.get("recovery_hint"),
                    "compromise_suspected": active_host_session.get("compromise_suspected"),
                },
            },
        )
    if active_web:
        nodes.insert(
            2,
            {
                "id": "bd_web_active",
                "label": active_web.get("origin") or active_web.get("title") or "Web Active",
                "kind": "web",
                "rail": active_web.get("trust_status", trust_status),
                "active": True,
                "meta": {
                    "tab_id": active_web.get("tab_id"),
                    "title": active_web.get("title"),
                    "browser": active_web.get("browser"),
                    "linked_surface_id": active_web.get("linked_surface", {}).get("surface_id"),
                    "link_confidence": active_web.get("linked_surface", {}).get("link_confidence", "none"),
                },
            },
        )
        nodes.insert(
            3,
            {
                "id": "bd_binding_active",
                "label": f"Bind:{binding.get('link_confidence', 'none')}",
                "kind": "binding",
                "rail": "trusted" if binding.get("link_confidence") in {"high", "medium"} else "0rail",
                "active": bool(binding.get("surface_id")),
                "meta": {
                    "linked_surface_id": binding.get("surface_id"),
                    "linked_surface_title": binding.get("window_title"),
                    "link_confidence": binding.get("link_confidence", "none"),
                    "binding_used_in_trust": bool(active_web.get("binding_used_in_trust", False)),
                    "primary_reason": binding_reason,
                },
            },
        )
    if active_mindseye:
        nodes.insert(
            2,
            {
                "id": "bd_mindseye_active",
                "label": active_mindseye.get("context_summary") or active_mindseye.get("condition") or "AHK Context",
                "kind": "human_context",
                "rail": "0rail",
                "active": True,
                "meta": {
                    "condition": active_mindseye.get("condition"),
                    "stage": active_mindseye.get("stage"),
                    "context_summary": active_mindseye.get("context_summary"),
                    "focus_level": active_mindseye.get("focus_level"),
                    "stress_level": active_mindseye.get("stress_level"),
                    "intent_signal": active_mindseye.get("intent_signal"),
                    "binding_confidence": mindseye_binding.get("confidence", "none"),
                    "linked_surface_id": mindseye_binding.get("linked_surface_id"),
                    "linked_web_origin": mindseye_binding.get("linked_web_origin"),
                },
            },
        )
    if active_ahk_feedback:
        feedback_response = str(active_ahk_feedback.get("user_response") or "none").lower()
        feedback_rail = "trusted" if feedback_response == "continue" else "shifted" if feedback_response in {"decline", "timeout"} else "0rail"
        nodes.append(
            {
                "id": "bd_feedback_active",
                "label": f"Feedback:{feedback_response}",
                "kind": "feedback",
                "rail": feedback_rail,
                "active": True,
                "meta": {
                    "original_action": active_ahk_feedback.get("original_action"),
                    "original_rule": active_ahk_feedback.get("original_rule"),
                    "surface_id": active_ahk_feedback.get("surface_id"),
                    "web_origin": active_ahk_feedback.get("web_origin"),
                    "reason": active_ahk_feedback.get("reason"),
                },
            },
        )

    return {
        "projection_version": "alpha-v1",
        "rail_state": rail_state,
        "trust_status": trust_status,
        "policy": policy,
        "hot_node": (
            "bd_feedback_active"
            if active_ahk_feedback and str(active_ahk_feedback.get("user_response") or "").lower() in {"decline", "timeout"}
            else
            "bd_host_session_active"
            if active_host_session and active_host_session.get("compromise_suspected")
            else
            "bd_qtf_active"
            if active_qtf_execution and (
                not active_qtf_execution.get("success", False)
                or (not active_web and not active_surface)
            )
            else
            "bd_package_active"
            if active_package_install and not active_web and not active_surface
            else
            "bd_policy_active"
            if policy_action in {"review", "quarantine", "deny"}
            else "bd_web_active"
            if active_web
            else "bd_qtf_active"
            if active_qtf_execution
            else ("bd_surface_active" if active_surface else "bd_root")
        ),
        "summary": tags.get("summary"),
        "edges": (
            [
                {"from": "bd_surface_active", "to": "bd_binding_active", "kind": "binding"},
                {"from": "bd_binding_active", "to": "bd_web_active", "kind": "binding"},
            ]
            if active_web and binding.get("surface_id")
            else []
        )
        + (
            [{"from": "bd_root", "to": "bd_host_session_active", "kind": "boot"}]
            if active_host_session
            else []
        )
        + (
            [
                {"from": "bd_package_active", "to": "bd_qtf_active", "kind": "route"}
            ]
            if active_package_install
            and active_qtf_execution
            and active_package_install.get("qtf_label")
            and active_package_install.get("qtf_label") == active_qtf_execution.get("label")
            else []
        )
        + (
            [{"from": "bd_root", "to": "bd_qtf_active", "kind": "containment"}]
            if active_qtf_execution
            else []
        )
        + (
            [{"from": "bd_root", "to": "bd_package_active", "kind": "observe"}]
            if active_package_install
            else []
        )
        + (
            [{"from": "bd_mindseye_active", "to": "bd_surface_active", "kind": "human_context"}]
            if active_mindseye and mindseye_binding.get("linked_surface_id")
            else []
        )
        + (
            [{"from": "bd_policy_active", "to": "bd_feedback_active", "kind": "feedback"}]
            if active_ahk_feedback
            else []
        )
        + [{"from": "bd_root", "to": "bd_policy_active", "kind": "policy"}],
        "nodes": nodes,
    }


def project_busydawg(
    state_path: Path = LATEST_STATE_JSON,
    tags_path: Path = LATEST_TAGS_JSON,
    output_path: Path = BUSYDAWG_STATE_JSON,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    tags = json.loads(tags_path.read_text(encoding="utf-8")) if tags_path.exists() else {}
    projection = build_busydawg_projection(state, tags)
    output_path.write_text(dump_json(projection) + "\n", encoding="utf-8")
    return projection
