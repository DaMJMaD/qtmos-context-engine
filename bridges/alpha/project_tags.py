from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from .models import dump_json
from .paths import LATEST_STATE_JSON, LATEST_TAGS_JSON, ensure_runtime_dirs


def _overall_summary(
    *,
    overall_trust: str,
    active_web: dict[str, Any],
    active_surface: dict[str, Any],
    binding_used_in_trust: bool,
) -> str:
    web_summary = active_web.get("trust_summary")
    web_trust = active_web.get("trust_status", "unknown")
    surface_trust = active_surface.get("trust_status", "unknown")
    if overall_trust == "suspicious":
        return web_summary or "suspicious: observed mismatches require caution"
    if overall_trust == "shifted":
        return web_summary or "shifted: context changed and should be reviewed"
    if overall_trust == "trusted" and binding_used_in_trust and web_summary:
        return web_summary
    if overall_trust == "trusted" and surface_trust == "trusted" and web_trust == "unknown" and active_web:
        return "trusted: stable active surface; browser evidence remains neutral"
    if overall_trust == "trusted" and active_surface:
        return "trusted: stable active surface"
    return "unknown: insufficient evidence"


def build_tags(state: dict[str, Any]) -> dict[str, Any]:
    active_surface = state.get("active_surface") or {}
    previous_surface = state.get("previous_active_surface") or {}
    active_web = state.get("active_web") or {}
    previous_web = state.get("previous_active_web") or {}
    active_mindseye = state.get("active_mindseye") or {}
    active_ahk_feedback = state.get("active_ahk_feedback") or {}
    active_qtf_execution = state.get("active_qtf_execution") or {}
    active_package_install = state.get("active_package_install") or {}
    active_host_session = state.get("active_host_session") or {}
    active_privilege = state.get("active_privilege") or {}
    mindseye_binding = active_mindseye.get("binding") or {}
    web_binding = active_web.get("linked_surface") or {}
    web_trust_reasons = active_web.get("trust_reasons", [])
    binding_used_in_trust = bool(active_web.get("binding_used_in_trust", False))
    surface_trust = active_surface.get("trust_status", "unknown")
    web_trust = active_web.get("trust_status", "unknown")
    trust_values = {surface_trust, web_trust}
    if "suspicious" in trust_values:
        trust = "suspicious"
    elif "shifted" in trust_values:
        trust = "shifted"
    elif "trusted" in trust_values:
        trust = "trusted"
    else:
        trust = "unknown"
    drift_flags = list(active_surface.get("drift_flags", [])) + list(active_web.get("drift_flags", []))
    mismatch_flags = list(active_surface.get("mismatch_flags", [])) + list(active_web.get("mismatch_flags", []))

    tags = ["state_rebuilt"]
    rails = {
        "0rail": {"raw_state": "latest active projection"},
        "-rail": {"risk": "none", "stale": False, "conflict": False},
        "+rail": {"meaning": "stable", "action_hint": "observe"},
        "pm_rail": {"fused_state": "neutral", "confidence": 0.75},
    }

    if trust == "trusted":
        tags.extend(["surface_trusted", "host_identity"])
        rails["+rail"] = {"meaning": "stable_active_surface", "action_hint": "allow_context_binding"}
        rails["pm_rail"] = {"fused_state": "surface_verified", "confidence": 0.98}
    elif trust == "shifted":
        tags.extend(["surface_shifted", "drift_detected"])
        rails["-rail"] = {"risk": "shifted", "stale": False, "conflict": True}
        rails["+rail"] = {"meaning": "surface_changed", "action_hint": "rebind_or_review"}
        rails["pm_rail"] = {"fused_state": "shifted_surface", "confidence": 0.82}
    elif trust == "suspicious":
        tags.extend(["surface_suspicious", "trust_warning"])
        rails["-rail"] = {"risk": "suspicious", "stale": False, "conflict": True}
        rails["+rail"] = {"meaning": "surface_mismatch", "action_hint": "warn_and_restrict"}
        rails["pm_rail"] = {"fused_state": "surface_alert", "confidence": 0.9}
    else:
        tags.append("surface_unknown")
        rails["-rail"] = {"risk": "unknown", "stale": False, "conflict": False}
        rails["+rail"] = {"meaning": "awaiting_trust", "action_hint": "observe_more"}
        rails["pm_rail"] = {"fused_state": "unknown_surface", "confidence": 0.5}

    if previous_surface:
        tags.append("focus_changed")
    if surface_trust == "trusted":
        tags.append("surface_trusted")
    elif surface_trust == "shifted":
        tags.append("surface_shifted")
    elif surface_trust == "suspicious":
        tags.append("surface_suspicious")
    if active_web:
        tags.append("web_active")
        tags.append(f"web_trust:{web_trust}")
        if web_trust == "trusted":
            tags.append("web_trusted")
        elif web_trust == "shifted":
            tags.append("web_shifted")
        elif web_trust == "suspicious":
            tags.append("web_suspicious")
        else:
            tags.append("web_unknown")
    link_confidence = web_binding.get("link_confidence", "none")
    if active_web:
        tags.append(f"link_confidence:{link_confidence}")
        if link_confidence in {"high", "medium", "low"}:
            tags.append("surface_web_bound")
        else:
            tags.append("surface_web_unbound")
    if previous_web:
        tags.append("web_changed")
    if active_mindseye:
        tags.append("human_context_active")
        if active_mindseye.get("stage"):
            tags.append(f"context_stage:{active_mindseye['stage']}")
        if active_mindseye.get("condition"):
            tags.append(f"context_condition:{str(active_mindseye['condition']).lower()}")
        tags.append(f"context_link:{mindseye_binding.get('confidence', 'none')}")
        if mindseye_binding.get("linked_surface_id"):
            tags.append("human_context_surface_bound")
    if active_ahk_feedback:
        tags.append("ahk_feedback_active")
        if active_ahk_feedback.get("user_response"):
            tags.append(f"ahk_feedback_response:{str(active_ahk_feedback['user_response']).lower()}")
        if active_ahk_feedback.get("original_action"):
            tags.append(f"ahk_feedback_action:{str(active_ahk_feedback['original_action']).lower()}")
    if active_qtf_execution:
        tags.append("qtf_active")
        if active_qtf_execution.get("backend"):
            tags.append(f"qtf_backend:{str(active_qtf_execution['backend']).lower()}")
        if active_qtf_execution.get("success"):
            tags.append("qtf_success")
        else:
            tags.append("qtf_failed")
        if active_qtf_execution.get("created_files") or active_qtf_execution.get("modified_files") or active_qtf_execution.get("deleted_files"):
            tags.append("qtf_workspace_changed")
    if active_package_install:
        tags.append("package_active")
        if active_package_install.get("manager"):
            tags.append(f"package_manager:{str(active_package_install['manager']).lower()}")
        if active_package_install.get("operation"):
            tags.append(f"package_operation:{str(active_package_install['operation']).lower()}")
        if active_package_install.get("source_kind"):
            tags.append(f"package_source:{str(active_package_install['source_kind']).lower()}")
        if active_package_install.get("qtf_requested"):
            tags.append("package_qtf_requested")
    if active_host_session:
        tags.append("host_session_active")
        if active_host_session.get("stage"):
            tags.append(f"host_stage:{str(active_host_session['stage']).lower()}")
        if active_host_session.get("session_type"):
            tags.append(f"host_session_type:{str(active_host_session['session_type']).lower()}")
        if active_host_session.get("current_desktop"):
            tags.append(f"host_desktop:{str(active_host_session['current_desktop']).lower()}")
        if active_host_session.get("compromise_suspected"):
            tags.append("host_compromise_suspected")
        if active_host_session.get("recovery_hint"):
            tags.append(f"host_recovery_hint:{str(active_host_session['recovery_hint']).lower()}")
    if active_privilege:
        tags.append("privilege_active")
        if active_privilege.get("method"):
            tags.append(f"privilege_method:{str(active_privilege['method']).lower()}")
        if active_privilege.get("result"):
            tags.append(f"privilege_result:{str(active_privilege['result']).lower()}")
        if active_privilege.get("target_user"):
            tags.append(f"privilege_target:{str(active_privilege['target_user']).lower()}")

    if drift_flags:
        tags.extend(f"drift:{flag}" for flag in drift_flags)
    if mismatch_flags:
        tags.extend(f"mismatch:{flag}" for flag in mismatch_flags)

    binding_evidence = {
        "web_trust_status": web_trust,
        "linked_surface_id": web_binding.get("surface_id"),
        "linked_surface_title": web_binding.get("window_title"),
        "link_confidence": link_confidence,
        "match_signals": web_binding.get("match_signals", []),
        "mismatch_signals": web_binding.get("mismatch_signals", []),
        "binding_used_in_trust": binding_used_in_trust,
        "trust_reasons": web_trust_reasons,
    }
    summary = _overall_summary(
        overall_trust=trust,
        active_web=active_web,
        active_surface=active_surface,
        binding_used_in_trust=binding_used_in_trust,
    )

    return {
        "status": "projected",
        "active_surface_id": active_surface.get("surface_id"),
        "active_surface_title": active_surface.get("window_title"),
        "previous_surface_id": previous_surface.get("surface_id"),
        "active_web_origin": active_web.get("origin"),
        "active_web_title": active_web.get("title"),
        "active_web_linked_surface_id": web_binding.get("surface_id"),
        "active_web_link_confidence": link_confidence,
        "previous_web_origin": previous_web.get("origin"),
        "active_context_condition": active_mindseye.get("condition"),
        "active_context_stage": active_mindseye.get("stage"),
        "active_context_binding_confidence": mindseye_binding.get("confidence", "none"),
        "active_context_surface_id": mindseye_binding.get("linked_surface_id"),
        "active_ahk_feedback_response": active_ahk_feedback.get("user_response"),
        "active_ahk_feedback_action": active_ahk_feedback.get("original_action"),
        "active_ahk_feedback_surface_id": active_ahk_feedback.get("surface_id"),
        "active_qtf_label": active_qtf_execution.get("label"),
        "active_qtf_backend": active_qtf_execution.get("backend"),
        "active_qtf_success": active_qtf_execution.get("success"),
        "active_package_manager": active_package_install.get("manager"),
        "active_package_name": active_package_install.get("package_name"),
        "active_package_qtf_requested": active_package_install.get("qtf_requested"),
        "active_host_stage": active_host_session.get("stage"),
        "active_host_boot_id": active_host_session.get("boot_id"),
        "active_host_compromise_suspected": active_host_session.get("compromise_suspected"),
        "active_host_recovery_hint": active_host_session.get("recovery_hint"),
        "active_privilege_method": active_privilege.get("method"),
        "active_privilege_result": active_privilege.get("result"),
        "active_privilege_target_user": active_privilege.get("target_user"),
        "last_focus_change_ts": state.get("last_focus_change_ts"),
        "last_web_change_ts": state.get("last_web_change_ts"),
        "last_ahk_feedback_ts": state.get("last_ahk_feedback_ts"),
        "last_qtf_execution_ts": state.get("last_qtf_execution_ts"),
        "last_package_install_ts": state.get("last_package_install_ts"),
        "last_host_session_ts": state.get("last_host_session_ts"),
        "last_privilege_ts": state.get("last_privilege_ts"),
        "trust_status": trust,
        "binding_evidence": binding_evidence,
        "trust_reasons": web_trust_reasons,
        "summary": summary,
        "tags": sorted(set(tags)),
        "rails": rails,
    }


def project_tags(
    state_path: Path = LATEST_STATE_JSON,
    output_path: Path = LATEST_TAGS_JSON,
) -> dict[str, Any]:
    ensure_runtime_dirs()
    if not state_path.exists():
        state: dict[str, Any] = {}
    else:
        state = json.loads(state_path.read_text(encoding="utf-8"))
    tags = build_tags(state)
    output_path.write_text(dump_json(tags) + "\n", encoding="utf-8")
    return tags
