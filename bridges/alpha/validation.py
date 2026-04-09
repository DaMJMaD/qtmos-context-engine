from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .ahk_feedback import build_ahk_feedback_event
from .ext import build_ext_event
from .host_session import build_host_session_event
from .mindseye import build_mindseye_event
from .models import normalize_event
from .privilege import build_privilege_event
from .policy import decide_policy
from .project_busydawg import build_busydawg_projection
from .project_tags import build_tags
from .package import build_package_install_event
from .qtf import build_qtf_event
from .reporting import build_report_payload
from .rebuild_state import build_state
from .surface import build_surface_event
from .web import build_web_event


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _scenario_files(scenarios_dir: Path) -> list[Path]:
    return sorted(path for path in scenarios_dir.glob("*.json") if path.is_file())


def _surface_event_from_config(config: dict[str, Any], previous_surface: dict[str, Any] | None) -> dict[str, Any]:
    event = build_surface_event(
        host=config.get("host", "scenario-runner"),
        workspace=config.get("workspace", "scenario"),
        session=config.get("session", "validation"),
        observer_id=config.get("observer_id", "scenario-surface"),
        host_kind=config.get("host_kind", "desktop"),
        label=config.get("label", "active_surface"),
        observation=dict(config.get("observation", {})),
        previous_surface=previous_surface,
    )
    if config.get("trust_status"):
        event["payload"]["trust_state"]["status"] = config["trust_status"]
        event["payload"]["trust_state"]["drift_flags"] = config.get("drift_flags", [])
        event["payload"]["trust_state"]["mismatch_flags"] = config.get("mismatch_flags", [])
    return event


def _web_event_from_config(
    config: dict[str, Any],
    *,
    candidate_surface: dict[str, Any] | None,
    previous_web: dict[str, Any] | None,
) -> dict[str, Any]:
    event = build_web_event(
        host=config.get("host", "scenario-runner"),
        workspace=config.get("workspace", "scenario"),
        session=config.get("session", "validation"),
        observer_id=config.get("observer_id", "scenario-web"),
        browser=config.get("browser", "chrome"),
        url=config.get("url", ""),
        title=config.get("title", ""),
        text_snippet=config.get("text_snippet", ""),
        tab_id=int(config.get("tab_id", 0) or 0),
        window_id=int(config.get("window_id", 0) or 0),
        mutated=bool(config.get("mutated", False)),
        visible=bool(config.get("visible", True)),
        linked_surface=dict(config.get("linked_surface", {})),
        candidate_surface=candidate_surface,
        previous_web=previous_web,
    )
    return event


def _mindseye_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_mindseye_event(
        {
            "ts": config.get("ts", "2026-04-08T16:55:00"),
            "channel": config.get("channel", "mindseye"),
            "source": config.get("source", "MindsEye"),
            "subject": config.get("subject", "vitals"),
            "payload": dict(config.get("payload", {})),
        },
        share_root=Path(config.get("share_root", "/tmp/qtmos-share")),
        channel=config.get("channel", "mindseye"),
    )


def _ahk_feedback_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_ahk_feedback_event(
        {
            "ts": config.get("ts", "2026-04-08T18:25:00Z"),
            "channel": config.get("channel", "ahk-feedback"),
            "source": config.get("source", "QTMoSPolicyHook"),
            "subject": config.get("subject", "review_response"),
            "payload": dict(config.get("payload", {})),
        },
        share_root=Path(config.get("share_root", "/tmp/qtmos-share")),
        channel=config.get("channel", "ahk-feedback"),
    )


def _qtf_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    execution = {
        "label": config.get("label", "local-offline-cage"),
        "backend_requested": config.get("backend_requested", "auto"),
        "backend": config.get("backend", "podman"),
        "backend_note": config.get("backend_note", "scenario"),
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
        "capture_ts": config.get("capture_ts", "2026-04-08T19:10:00Z"),
    }
    return build_qtf_event(execution)


def _package_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
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


def _host_session_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_host_session_event(
        stage=config.get("stage", "gnome-handoff"),
        compromise_suspected=bool(config.get("compromise_suspected", False)),
        suspicion_note=config.get("suspicion_note", ""),
        recovery_hint=config.get("recovery_hint", "observe_only"),
    )


def _privilege_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_privilege_event(
        method=config.get("method", "sudo"),
        result=config.get("result", "prompted"),
        target_user=config.get("target_user", "root"),
        target_uid=config.get("target_uid", 0),
        reason=config.get("reason", ""),
        command=list(config.get("command", [])),
    )


def _ext_event_from_config(config: dict[str, Any]) -> dict[str, Any]:
    return build_ext_event(
        result=config.get("result", "requested"),
        target=config.get("target", "host"),
        artifact_kind=config.get("artifact_kind", "package"),
        qtf_label=config.get("qtf_label", ""),
        package_name=config.get("package_name", ""),
        package_manager=config.get("package_manager", ""),
        reason=config.get("reason", ""),
    )


def _evaluate_expectations(expected: dict[str, Any], report: dict[str, Any], state: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    binding = report.get("binding", {})
    active_web = state.get("active_web") or {}

    if "overall_trust" in expected and report.get("overall_status") != expected["overall_trust"]:
        failures.append(f"overall_trust expected {expected['overall_trust']} got {report.get('overall_status')}")
    if "web_trust" in expected and report.get("active_web", {}).get("web_trust") != expected["web_trust"]:
        failures.append(f"web_trust expected {expected['web_trust']} got {report.get('active_web', {}).get('web_trust')}")
    if "binding_confidence" in expected and binding.get("link_confidence") != expected["binding_confidence"]:
        failures.append(f"binding_confidence expected {expected['binding_confidence']} got {binding.get('link_confidence')}")
    if "binding_used_in_trust" in expected and bool(binding.get("binding_used_in_trust")) != bool(expected["binding_used_in_trust"]):
        failures.append(
            f"binding_used_in_trust expected {expected['binding_used_in_trust']} got {binding.get('binding_used_in_trust')}"
        )

    reasons = set(binding.get("trust_reasons") or [])
    mismatches = set(active_web.get("mismatch_flags") or [])
    drifts = set(active_web.get("drift_flags") or [])

    for reason in expected.get("trust_reasons_include", []):
        if reason not in reasons:
            failures.append(f"missing trust reason {reason}")
    for flag in expected.get("mismatch_flags_include", []):
        if flag not in mismatches:
            failures.append(f"missing mismatch flag {flag}")
    for flag in expected.get("drift_flags_include", []):
        if flag not in drifts:
            failures.append(f"missing drift flag {flag}")

    return (not failures), failures


def _evaluate_policy_expectations(expected: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    if "policy_action" in expected and policy.get("action") != expected["policy_action"]:
        failures.append(f"policy_action expected {expected['policy_action']} got {policy.get('action')}")
    if "policy_rule" in expected and policy.get("policy_rule") != expected["policy_rule"]:
        failures.append(f"policy_rule expected {expected['policy_rule']} got {policy.get('policy_rule')}")
    return failures


def run_browser_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    state = build_state(events)

    surface_cfg = scenario.get("surface")
    if surface_cfg:
        events.append(normalize_event(_surface_event_from_config(surface_cfg, state.get("active_surface"))))
        state = build_state(events)

    for prelude in scenario.get("prelude_web", []):
        events.append(
            normalize_event(
                _web_event_from_config(
                    prelude,
                    candidate_surface=state.get("active_surface"),
                    previous_web=state.get("active_web"),
                )
            )
        )
        state = build_state(events)

    events.append(
        normalize_event(
            _web_event_from_config(
                scenario.get("web", {}),
                candidate_surface=state.get("active_surface"),
                previous_web=state.get("active_web"),
            )
        )
    )
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    passed, failures = _evaluate_expectations(scenario.get("expected", {}), report, state)
    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": passed,
        "failures": failures,
        "expected": scenario.get("expected", {}),
        "actual": {
            "overall_trust": report.get("overall_status"),
            "web_trust": report.get("active_web", {}).get("web_trust"),
            "binding_confidence": report.get("binding", {}).get("link_confidence"),
            "binding_used_in_trust": report.get("binding", {}).get("binding_used_in_trust"),
            "trust_reasons": report.get("binding", {}).get("trust_reasons", []),
            "mismatch_flags": state.get("active_web", {}).get("mismatch_flags", []),
            "drift_flags": state.get("active_web", {}).get("drift_flags", []),
            "summary": report.get("summary"),
        },
    }


def validate_browser_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_browser_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_mindseye_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    state = build_state(events)

    surface_cfg = scenario.get("surface")
    if surface_cfg:
        events.append(normalize_event(_surface_event_from_config(surface_cfg, state.get("active_surface"))))
        state = build_state(events)

    web_cfg = scenario.get("web")
    if web_cfg:
        events.append(
            normalize_event(
                _web_event_from_config(
                    web_cfg,
                    candidate_surface=state.get("active_surface"),
                    previous_web=state.get("active_web"),
                )
            )
        )
        state = build_state(events)

    mindseye_cfg = scenario.get("mindseye", {})
    events.append(normalize_event(_mindseye_event_from_config(mindseye_cfg)))
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    binding = (state.get("active_mindseye") or {}).get("binding") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "mindseye_binding_confidence" in expected and binding.get("confidence") != expected["mindseye_binding_confidence"]:
        failures.append(
            f"mindseye_binding_confidence expected {expected['mindseye_binding_confidence']} got {binding.get('confidence')}"
        )
    if "mindseye_surface_id" in expected and binding.get("linked_surface_id") != expected["mindseye_surface_id"]:
        failures.append(f"mindseye_surface_id expected {expected['mindseye_surface_id']} got {binding.get('linked_surface_id')}")
    if "mindseye_web_origin" in expected and binding.get("linked_web_origin") != expected["mindseye_web_origin"]:
        failures.append(f"mindseye_web_origin expected {expected['mindseye_web_origin']} got {binding.get('linked_web_origin')}")
    for reason in expected.get("reasons_include", []):
        if reason not in set(binding.get("reasons") or []):
            failures.append(f"missing binding reason {reason}")

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "mindseye_binding_confidence": binding.get("confidence"),
            "mindseye_surface_id": binding.get("linked_surface_id"),
            "mindseye_web_origin": binding.get("linked_web_origin"),
            "reasons": binding.get("reasons", []),
            "summary": report.get("summary"),
        },
    }


def validate_mindseye_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_mindseye_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_ahk_feedback_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    state = build_state(events)

    surface_cfg = scenario.get("surface")
    if surface_cfg:
        events.append(normalize_event(_surface_event_from_config(surface_cfg, state.get("active_surface"))))
        state = build_state(events)

    web_cfg = scenario.get("web")
    if web_cfg:
        events.append(
            normalize_event(
                _web_event_from_config(
                    web_cfg,
                    candidate_surface=state.get("active_surface"),
                    previous_web=state.get("active_web"),
                )
            )
        )
        state = build_state(events)

    mindseye_cfg = scenario.get("mindseye")
    if mindseye_cfg:
        events.append(normalize_event(_mindseye_event_from_config(mindseye_cfg)))
        state = build_state(events)

    feedback_cfg = scenario.get("feedback", {})
    events.append(normalize_event(_ahk_feedback_event_from_config(feedback_cfg)))
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    feedback = report.get("active_ahk_feedback") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "user_response" in expected and feedback.get("user_response") != expected["user_response"]:
        failures.append(f"user_response expected {expected['user_response']} got {feedback.get('user_response')}")
    if "original_action" in expected and feedback.get("original_action") != expected["original_action"]:
        failures.append(f"original_action expected {expected['original_action']} got {feedback.get('original_action')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "user_response": feedback.get("user_response"),
            "original_action": feedback.get("original_action"),
            "hot_node": busydawg.get("hot_node"),
            "summary": report.get("summary"),
        },
    }


def validate_ahk_feedback_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_ahk_feedback_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_full_chain_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    state = build_state(events)

    surface_cfg = scenario.get("surface")
    if surface_cfg:
        events.append(normalize_event(_surface_event_from_config(surface_cfg, state.get("active_surface"))))
        state = build_state(events)

    for prelude in scenario.get("prelude_web", []):
        events.append(
            normalize_event(
                _web_event_from_config(
                    prelude,
                    candidate_surface=state.get("active_surface"),
                    previous_web=state.get("active_web"),
                )
            )
        )
        state = build_state(events)

    web_cfg = scenario.get("web")
    if web_cfg:
        events.append(
            normalize_event(
                _web_event_from_config(
                    web_cfg,
                    candidate_surface=state.get("active_surface"),
                    previous_web=state.get("active_web"),
                )
            )
        )
        state = build_state(events)

    mindseye_cfg = scenario.get("mindseye")
    if mindseye_cfg:
        events.append(normalize_event(_mindseye_event_from_config(mindseye_cfg)))
        state = build_state(events)

    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)
    expected = scenario.get("expected", {})

    passed, failures = _evaluate_expectations(expected, report, state)
    failures.extend(_evaluate_policy_expectations(expected, report.get("policy") or {}))

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures and passed,
        "failures": failures,
        "expected": expected,
        "actual": {
            "overall_trust": report.get("overall_status"),
            "web_trust": report.get("active_web", {}).get("web_trust"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "policy_rule": (report.get("policy") or {}).get("policy_rule"),
            "binding_confidence": report.get("binding", {}).get("link_confidence"),
            "mindseye_binding": ((report.get("active_mindseye") or {}).get("binding") or {}).get("confidence"),
            "summary": report.get("summary"),
        },
    }


def validate_full_chain_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_full_chain_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_policy_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    state = dict(scenario.get("state_snapshot", {}))
    tags = dict(scenario.get("tags_snapshot", {}))
    policy = decide_policy(state, tags)
    expected = scenario.get("expected", {})
    failures: list[str] = []

    failures.extend(_evaluate_policy_expectations(expected, policy))

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "policy_action": policy.get("action"),
            "policy_rule": policy.get("policy_rule"),
            "reason": policy.get("reason"),
        },
    }


def validate_policy_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_policy_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_qtf_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events = [normalize_event(_qtf_event_from_config(scenario.get("qtf", {})))]
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    qtf = report.get("active_qtf_execution") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "qtf_success" in expected and bool(qtf.get("success")) != bool(expected["qtf_success"]):
        failures.append(f"qtf_success expected {expected['qtf_success']} got {qtf.get('success')}")
    if "qtf_backend" in expected and qtf.get("backend") != expected["qtf_backend"]:
        failures.append(f"qtf_backend expected {expected['qtf_backend']} got {qtf.get('backend')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")

    created = set(qtf.get("created_files") or [])
    modified = set(qtf.get("modified_files") or [])
    deleted = set(qtf.get("deleted_files") or [])
    for path in expected.get("created_files_include", []):
        if path not in created:
            failures.append(f"missing created file {path}")
    for path in expected.get("modified_files_include", []):
        if path not in modified:
            failures.append(f"missing modified file {path}")
    for path in expected.get("deleted_files_include", []):
        if path not in deleted:
            failures.append(f"missing deleted file {path}")

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "qtf_success": qtf.get("success"),
            "qtf_backend": qtf.get("backend"),
            "created_files": qtf.get("created_files", []),
            "modified_files": qtf.get("modified_files", []),
            "deleted_files": qtf.get("deleted_files", []),
            "hot_node": busydawg.get("hot_node"),
        },
    }


def validate_qtf_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_qtf_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_package_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    package_cfg = scenario.get("package")
    if package_cfg:
        events.append(normalize_event(_package_event_from_config(package_cfg)))
    qtf_cfg = scenario.get("qtf")
    if qtf_cfg:
        events.append(normalize_event(_qtf_event_from_config(qtf_cfg)))
    ext_cfg = scenario.get("ext")
    if ext_cfg:
        events.append(normalize_event(_ext_event_from_config(ext_cfg)))

    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    package = report.get("active_package_install") or {}
    qtf = report.get("active_qtf_execution") or {}
    ext = report.get("active_ext_promotion") or {}
    policy = report.get("policy") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "package_manager" in expected and package.get("manager") != expected["package_manager"]:
        failures.append(f"package_manager expected {expected['package_manager']} got {package.get('manager')}")
    if "package_qtf_requested" in expected and bool(package.get("qtf_requested")) != bool(expected["package_qtf_requested"]):
        failures.append(f"package_qtf_requested expected {expected['package_qtf_requested']} got {package.get('qtf_requested')}")
    if "qtf_backend" in expected and qtf.get("backend") != expected["qtf_backend"]:
        failures.append(f"qtf_backend expected {expected['qtf_backend']} got {qtf.get('backend')}")
    if "qtf_success" in expected and bool(qtf.get("success")) != bool(expected["qtf_success"]):
        failures.append(f"qtf_success expected {expected['qtf_success']} got {qtf.get('success')}")
    if "ext_result" in expected and ext.get("result") != expected["ext_result"]:
        failures.append(f"ext_result expected {expected['ext_result']} got {ext.get('result')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")
    failures.extend(_evaluate_policy_expectations(expected, policy))

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "package_manager": package.get("manager"),
            "package_qtf_requested": package.get("qtf_requested"),
            "qtf_backend": qtf.get("backend"),
            "qtf_success": qtf.get("success"),
            "ext_result": ext.get("result"),
            "hot_node": busydawg.get("hot_node"),
            "policy_action": policy.get("action"),
            "policy_rule": policy.get("policy_rule"),
        },
    }


def validate_package_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_package_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_host_session_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events = [normalize_event(_host_session_event_from_config(scenario.get("host_session", {})))]
    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    host_session = report.get("active_host_session") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "stage" in expected and host_session.get("stage") != expected["stage"]:
        failures.append(f"stage expected {expected['stage']} got {host_session.get('stage')}")
    if "compromise_suspected" in expected and bool(host_session.get("compromise_suspected")) != bool(expected["compromise_suspected"]):
        failures.append(
            f"compromise_suspected expected {expected['compromise_suspected']} got {host_session.get('compromise_suspected')}"
        )
    if "recovery_hint" in expected and host_session.get("recovery_hint") != expected["recovery_hint"]:
        failures.append(f"recovery_hint expected {expected['recovery_hint']} got {host_session.get('recovery_hint')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "stage": host_session.get("stage"),
            "compromise_suspected": host_session.get("compromise_suspected"),
            "recovery_hint": host_session.get("recovery_hint"),
            "hot_node": busydawg.get("hot_node"),
        },
    }


def validate_host_session_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_host_session_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_privilege_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    host_session_cfg = scenario.get("host_session")
    if host_session_cfg:
        events.append(normalize_event(_host_session_event_from_config(host_session_cfg)))
    privilege_cfg = scenario.get("privilege", {})
    events.append(normalize_event(_privilege_event_from_config(privilege_cfg)))

    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    privilege = report.get("active_privilege") or {}
    policy = report.get("policy") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "method" in expected and privilege.get("method") != expected["method"]:
        failures.append(f"method expected {expected['method']} got {privilege.get('method')}")
    if "result" in expected and privilege.get("result") != expected["result"]:
        failures.append(f"result expected {expected['result']} got {privilege.get('result')}")
    if "target_user" in expected and privilege.get("target_user") != expected["target_user"]:
        failures.append(f"target_user expected {expected['target_user']} got {privilege.get('target_user')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")
    failures.extend(_evaluate_policy_expectations(expected, policy))

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "method": privilege.get("method"),
            "result": privilege.get("result"),
            "target_user": privilege.get("target_user"),
            "hot_node": busydawg.get("hot_node"),
            "policy_action": policy.get("action"),
            "policy_rule": policy.get("policy_rule"),
        },
    }


def validate_privilege_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_privilege_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }


def run_ext_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    host_session_cfg = scenario.get("host_session")
    if host_session_cfg:
        events.append(normalize_event(_host_session_event_from_config(host_session_cfg)))
    package_cfg = scenario.get("package")
    if package_cfg:
        events.append(normalize_event(_package_event_from_config(package_cfg)))
    qtf_cfg = scenario.get("qtf")
    if qtf_cfg:
        events.append(normalize_event(_qtf_event_from_config(qtf_cfg)))
    ext_cfg = scenario.get("ext", {})
    events.append(normalize_event(_ext_event_from_config(ext_cfg)))

    state = build_state(events)
    tags = build_tags(state)
    busydawg = build_busydawg_projection(state, tags)
    report = build_report_payload(state, tags, busydawg)

    ext = report.get("active_ext_promotion") or {}
    policy = report.get("policy") or {}
    expected = scenario.get("expected", {})
    failures: list[str] = []

    if "result" in expected and ext.get("result") != expected["result"]:
        failures.append(f"result expected {expected['result']} got {ext.get('result')}")
    if "target" in expected and ext.get("target") != expected["target"]:
        failures.append(f"target expected {expected['target']} got {ext.get('target')}")
    if "qtf_label" in expected and ext.get("qtf_label") != expected["qtf_label"]:
        failures.append(f"qtf_label expected {expected['qtf_label']} got {ext.get('qtf_label')}")
    if "hot_node" in expected and busydawg.get("hot_node") != expected["hot_node"]:
        failures.append(f"hot_node expected {expected['hot_node']} got {busydawg.get('hot_node')}")
    failures.extend(_evaluate_policy_expectations(expected, policy))

    return {
        "id": scenario.get("id", "unnamed"),
        "name": scenario.get("name", scenario.get("id", "unnamed")),
        "passed": not failures,
        "failures": failures,
        "expected": expected,
        "actual": {
            "result": ext.get("result"),
            "target": ext.get("target"),
            "qtf_label": ext.get("qtf_label"),
            "hot_node": busydawg.get("hot_node"),
            "policy_action": policy.get("action"),
            "policy_rule": policy.get("policy_rule"),
        },
    }


def validate_ext_scenarios(scenarios_dir: Path) -> dict[str, Any]:
    results = [run_ext_scenario(_load_json(path)) for path in _scenario_files(scenarios_dir)]
    passed = sum(1 for item in results if item["passed"])
    return {
        "scenario_dir": str(scenarios_dir),
        "scenario_count": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
