from __future__ import annotations

import json
from typing import Any

from .paths import CONFIG_DIR, POLICY_RULES_JSON


DEFAULT_POLICY_RULES: list[dict[str, Any]] = [
    {
        "name": "host_lockdown_privilege_deny",
        "host_compromise_suspected": True,
        "host_recovery_hint": "lockdown_ready",
        "privilege_active": True,
        "privilege_result": "granted",
        "action": "deny",
        "reason": "Privilege escalation during a suspected host session should be denied",
    },
    {
        "name": "host_lockdown_ext_deny",
        "host_compromise_suspected": True,
        "host_recovery_hint": "lockdown_ready",
        "ext_active": True,
        "ext_result": "requested",
        "action": "deny",
        "reason": "Promotion requests during a lockdown-ready suspicious host session should be denied",
    },
    {
        "name": "host_suspected_privilege_review",
        "host_compromise_suspected": True,
        "privilege_active": True,
        "action": "review",
        "reason": "Privilege boundary during a suspected host session requires review",
    },
    {
        "name": "host_suspected_ext_review",
        "host_compromise_suspected": True,
        "ext_active": True,
        "ext_result": "requested",
        "action": "review",
        "reason": "Promotion gate activity during a suspected host session requires review",
    },
    {
        "name": "package_qtf_fail_quarantine",
        "package_qtf_requested": True,
        "qtf_success": False,
        "action": "quarantine",
        "reason": "QTF execution failed and the package flow should stay contained",
    },
    {
        "name": "package_ext_denied_quarantine",
        "ext_active": True,
        "ext_result": "denied",
        "action": "quarantine",
        "reason": "Denied EXT promotion should stay contained inside QTF",
    },
    {
        "name": "ext_unmatched_review",
        "ext_active": True,
        "ext_result": "requested",
        "ext_matches_qtf": False,
        "action": "review",
        "reason": "Promotion request without matched QTF evidence requires review",
    },
    {
        "name": "package_registry_review",
        "package_source_kind": "registry",
        "action": "review",
        "reason": "Registry-sourced package requires review before promotion",
    },
    {
        "name": "package_no_lockfile_review",
        "package_lockfile_state": "missing",
        "action": "review",
        "reason": "Package flow has no lockfile and should be reviewed before promotion",
    },
    {
        "name": "package_scripts_host_review",
        "package_scripts_policy": "default",
        "package_qtf_requested": False,
        "action": "review",
        "reason": "Install scripts remain enabled outside QTF and need review",
    },
    {
        "name": "package_ext_required_review",
        "package_promotion_pending": True,
        "action": "review",
        "reason": "Contained package flow requires an explicit EXT promotion request before host use",
    },
    {
        "name": "package_clean_local_ext_allow",
        "package_source_kind": "local",
        "package_qtf_requested": True,
        "qtf_success": True,
        "ext_active": True,
        "ext_result": "requested",
        "ext_target": "host",
        "ext_matches_qtf": True,
        "action": "allow",
        "reason": "Local package completed cleanly inside QTF and passed through EXT",
    },
    {
        "name": "hard_deny",
        "trust": "suspicious",
        "sensitive": True,
        "action": "deny",
        "reason": "Explicit high-risk pattern on a sensitive surface",
    },
    {
        "name": "trusted_clean",
        "trust": "trusted",
        "context_condition": ["STABLE"],
        "min_binding": 0.7,
        "action": "allow",
        "reason": "Clean host, stable user context, strong binding",
    },
    {
        "name": "trusted_bound_allow",
        "trust": "trusted",
        "min_binding": 0.7,
        "action": "allow",
        "reason": "Clean host and strong binding support normal flow",
    },
    {
        "name": "high_stress_mismatch",
        "trust": "shifted",
        "context_condition": ["HIGH_STRESS"],
        "action": "review",
        "reason": "User stress plus surface drift needs an explicit review",
    },
    {
        "name": "suspicious_sensitive",
        "trust": "suspicious",
        "action": "quarantine",
        "reason": "Sensitive page or strong mismatch requires containment",
    },
    {
        "name": "shifted_mild",
        "trust": "shifted",
        "action": "warn",
        "reason": "Host or identity drift detected",
    },
    {
        "name": "unknown_weak",
        "trust": "unknown",
        "action": "review",
        "reason": "Insufficient observation requires manual review",
    },
]


def _binding_to_score(value: Any) -> float:
    if isinstance(value, (int, float)):
        return float(value)

    normalized = str(value or "").strip().lower()
    mapping = {
        "none": 0.0,
        "low": 0.35,
        "medium": 0.65,
        "high": 0.9,
    }
    return mapping.get(normalized, 0.0)


def ensure_policy_rules_file() -> None:
    if POLICY_RULES_JSON.exists():
        return
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    POLICY_RULES_JSON.write_text(json.dumps(DEFAULT_POLICY_RULES, indent=2) + "\n", encoding="utf-8")


def load_policy_rules() -> list[dict[str, Any]]:
    ensure_policy_rules_file()
    try:
        raw = json.loads(POLICY_RULES_JSON.read_text(encoding="utf-8"))
    except Exception:
        return list(DEFAULT_POLICY_RULES)
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    return list(DEFAULT_POLICY_RULES)


def build_policy_context(state: dict[str, Any], tags: dict[str, Any]) -> dict[str, Any]:
    active_web = state.get("active_web") or {}
    active_surface = state.get("active_surface") or {}
    active_mindseye = state.get("active_mindseye") or {}
    active_package = state.get("active_package_install") or {}
    active_qtf = state.get("active_qtf_execution") or {}
    active_host_session = state.get("active_host_session") or {}
    active_privilege = state.get("active_privilege") or {}
    active_ext = state.get("active_ext_promotion") or {}
    mindseye_binding = active_mindseye.get("binding") or {}
    web_binding = tags.get("binding_evidence") or {}
    mismatch_flags = list(active_web.get("mismatch_flags", [])) + list(active_surface.get("mismatch_flags", []))
    drift_flags = list(active_web.get("drift_flags", [])) + list(active_surface.get("drift_flags", []))
    mindseye_context = mindseye_binding.get("context") or {}
    context_condition = str(
        active_mindseye.get("condition")
        or mindseye_context.get("user_state")
        or "UNKNOWN"
    ).upper()

    sensitive = "sensitive_flow_low_trust" in mismatch_flags
    package_ts = str(active_package.get("ts") or "")
    qtf_ts = str(active_qtf.get("ts") or "")
    qtf_label = str(active_package.get("qtf_label") or "")
    qtf_matches_package = bool(
        active_package
        and qtf_label
        and active_qtf.get("label") == qtf_label
        and (not package_ts or not qtf_ts or qtf_ts >= package_ts)
    )
    matched_qtf = active_qtf if qtf_matches_package else {}
    ext_ts = str(active_ext.get("ts") or "")
    ext_qtf_label = str(active_ext.get("qtf_label") or "")
    ext_matches_qtf = bool(
        active_ext
        and matched_qtf
        and ext_qtf_label
        and matched_qtf.get("label") == ext_qtf_label
        and (not qtf_ts or not ext_ts or ext_ts >= qtf_ts)
    )
    ext_matches_package = bool(
        ext_matches_qtf
        and active_package
        and qtf_label
        and qtf_label == ext_qtf_label
        and (not package_ts or not ext_ts or ext_ts >= package_ts)
    )
    matched_ext = active_ext if ext_matches_qtf and (not active_package or ext_matches_package) else {}
    package_promotion_pending = bool(
        active_package
        and active_package.get("qtf_requested")
        and matched_qtf.get("success") is True
        and not matched_ext
    )

    return {
        "timestamp": state.get("rebuilt_at"),
        "trust": tags.get("trust_status", "unknown"),
        "surface_trust": active_surface.get("trust_status", "unknown"),
        "web_trust": active_web.get("trust_status", "unknown"),
        "binding_confidence": _binding_to_score(web_binding.get("link_confidence")),
        "binding_confidence_label": web_binding.get("link_confidence", "none"),
        "mindseye_binding_confidence": _binding_to_score(mindseye_binding.get("confidence")),
        "mindseye_binding_confidence_label": mindseye_binding.get("confidence", "none"),
        "context_condition": context_condition,
        "mindseye_condition": context_condition,
        "host_compromise_suspected": bool(active_host_session.get("compromise_suspected", False)),
        "host_recovery_hint": active_host_session.get("recovery_hint"),
        "privilege_active": bool(active_privilege),
        "privilege_method": active_privilege.get("method"),
        "privilege_result": active_privilege.get("result"),
        "ext_active": bool(active_ext),
        "ext_result": active_ext.get("result"),
        "ext_target": active_ext.get("target"),
        "ext_artifact_kind": active_ext.get("artifact_kind"),
        "ext_qtf_label": active_ext.get("qtf_label"),
        "ext_matches_qtf": ext_matches_qtf,
        "package_promotion_pending": package_promotion_pending,
        "package_active": bool(active_package),
        "package_manager": active_package.get("manager"),
        "package_operation": active_package.get("operation"),
        "package_name": active_package.get("package_name"),
        "package_source_kind": active_package.get("source_kind"),
        "package_lockfile_state": active_package.get("lockfile_state"),
        "package_scripts_policy": active_package.get("scripts_policy"),
        "package_qtf_requested": bool(active_package.get("qtf_requested", False)),
        "qtf_success": matched_qtf.get("success"),
        "qtf_backend": matched_qtf.get("backend"),
        "active_mindseye": {
            "condition": active_mindseye.get("condition"),
            "stage": active_mindseye.get("stage"),
            "binding": mindseye_binding,
            "context": mindseye_context,
        },
        "active_package": active_package,
        "active_qtf_execution": matched_qtf,
        "active_host_session": active_host_session,
        "active_privilege": active_privilege,
        "active_ext_promotion": active_ext,
        "signals": {
            "sensitive_page": sensitive,
            "mismatch_flags": mismatch_flags,
            "drift_flags": drift_flags,
            "binding_used_in_trust": bool(active_web.get("binding_used_in_trust", False)),
        },
        "active_surface": {
            "surface_id": active_surface.get("surface_id"),
            "window_title": active_surface.get("window_title"),
            "process_name": active_surface.get("process_name"),
        },
        "active_web": {
            "origin": active_web.get("origin"),
            "title": active_web.get("title"),
        },
    }


def decide_policy(state: dict[str, Any], tags: dict[str, Any]) -> dict[str, Any]:
    context = build_policy_context(state, tags)
    rules = load_policy_rules()

    for rule in rules:
        if "trust" in rule and rule["trust"] != context["trust"]:
            continue
        if "sensitive" in rule and bool(rule["sensitive"]) != bool(context["signals"].get("sensitive_page")):
            continue
        if "min_binding" in rule and context["binding_confidence"] < float(rule["min_binding"]):
            continue
        allowed_conditions = rule.get("context_condition") or rule.get("mindseye_condition") or []
        if allowed_conditions and context["context_condition"] not in allowed_conditions:
            continue
        if "host_compromise_suspected" in rule and bool(rule["host_compromise_suspected"]) != bool(context.get("host_compromise_suspected")):
            continue
        if "host_recovery_hint" in rule and rule["host_recovery_hint"] != context.get("host_recovery_hint"):
            continue
        if "privilege_active" in rule and bool(rule["privilege_active"]) != bool(context.get("privilege_active")):
            continue
        if "privilege_method" in rule and rule["privilege_method"] != context.get("privilege_method"):
            continue
        if "privilege_result" in rule and rule["privilege_result"] != context.get("privilege_result"):
            continue
        if "ext_active" in rule and bool(rule["ext_active"]) != bool(context.get("ext_active")):
            continue
        if "ext_result" in rule and rule["ext_result"] != context.get("ext_result"):
            continue
        if "ext_target" in rule and rule["ext_target"] != context.get("ext_target"):
            continue
        if "ext_artifact_kind" in rule and rule["ext_artifact_kind"] != context.get("ext_artifact_kind"):
            continue
        if "ext_matches_qtf" in rule and bool(rule["ext_matches_qtf"]) != bool(context.get("ext_matches_qtf")):
            continue
        if "package_active" in rule and bool(rule["package_active"]) != bool(context.get("package_active")):
            continue
        if "package_manager" in rule and rule["package_manager"] != context.get("package_manager"):
            continue
        if "package_operation" in rule and rule["package_operation"] != context.get("package_operation"):
            continue
        if "package_source_kind" in rule and rule["package_source_kind"] != context.get("package_source_kind"):
            continue
        if "package_lockfile_state" in rule and rule["package_lockfile_state"] != context.get("package_lockfile_state"):
            continue
        if "package_scripts_policy" in rule and rule["package_scripts_policy"] != context.get("package_scripts_policy"):
            continue
        if "package_qtf_requested" in rule and bool(rule["package_qtf_requested"]) != bool(context.get("package_qtf_requested")):
            continue
        if "qtf_success" in rule and rule["qtf_success"] != context.get("qtf_success"):
            continue
        if "qtf_backend" in rule and rule["qtf_backend"] != context.get("qtf_backend"):
            continue
        if "package_promotion_pending" in rule and bool(rule["package_promotion_pending"]) != bool(context.get("package_promotion_pending")):
            continue

        return {
            "action": rule.get("action", "warn"),
            "policy_rule": rule.get("name", "unnamed_rule"),
            "reason": rule.get("reason", "Policy rule matched"),
            "applied_at": context.get("timestamp"),
            "context": context,
        }

    return {
        "action": "warn",
        "policy_rule": "default_fallback",
        "reason": "No policy rule matched, conservative warning default applied",
        "applied_at": context.get("timestamp"),
        "context": context,
    }
