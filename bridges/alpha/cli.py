from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .ahk_feedback import ingest_ahk_feedback_and_cycle, ingest_ahk_feedback_events
from .ahk_policy_bridge import publish_ahk_policy_hook
from .appender import append_event
from .ext import observe_ext_and_cycle
from .host_session import observe_host_session_and_cycle
from .models import dump_json, now_iso
from .paths import (
    AHK_FEEDBACK_SCENARIOS_DIR,
    AHK_LEARN_JSONL,
    AHK_RECORD_JSONL,
    BUSYDAWG_STATE_JSON,
    EXT_SCENARIOS_DIR,
    EVENTS_JSONL,
    FULL_CHAIN_SCENARIOS_DIR,
    HOST_SESSION_SCENARIOS_DIR,
    LATEST_STATE_JSON,
    LATEST_TAGS_JSON,
    MINDS_EYE_SCENARIOS_DIR,
    PACKAGE_SCENARIOS_DIR,
    POLICY_SCENARIOS_DIR,
    PRIVILEGE_SCENARIOS_DIR,
    QTF_SCENARIOS_DIR,
    SCENARIOS_DIR,
)
from .http_bridge import serve as serve_http_bridge
from .mindseye import ingest_mindseye_and_cycle
from .package import observe_package_install
from .privilege import observe_privilege_and_cycle
from .project_busydawg import project_busydawg
from .project_tags import project_tags
from .qtf import run_qtf_command
from .reporting import build_report_payload, dump_report_json, render_report_text
from .rebuild_state import rebuild_state
from .reset_runtime import reset_alpha
from .surface import append_surface_event, build_surface_event, load_previous_surface
from .validation import (
    validate_ahk_feedback_scenarios,
    validate_browser_scenarios,
    validate_ext_scenarios,
    validate_full_chain_scenarios,
    validate_host_session_scenarios,
    validate_mindseye_scenarios,
    validate_package_scenarios,
    validate_policy_scenarios,
    validate_privilege_scenarios,
    validate_qtf_scenarios,
)
from .web import append_web_event, build_web_event, load_previous_web


def _load_json_arg(raw: str) -> dict[str, Any]:
    path = Path(raw)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return json.loads(raw)


def _maybe_publish_ahk_hook(
    *,
    state: dict[str, Any],
    tags: dict[str, Any],
    projection: dict[str, Any],
    enabled: bool,
    share_root: str | None = None,
    channel: str = "ahk-policy",
) -> dict[str, Any] | None:
    if not enabled:
        return None
    report = build_report_payload(state, tags, projection)
    return publish_ahk_policy_hook(report, share_root=share_root, channel=channel)


def emit_surface_event(args: argparse.Namespace) -> dict[str, Any]:
    observation = {
        "platform": args.platform,
        "surface_id": args.surface_id,
        "pid": args.pid,
        "process_name": args.process_name,
        "process_path": args.process_path,
        "window_class": args.window_class,
        "window_title": args.window_title,
        "bounds": {
            "x": args.x,
            "y": args.y,
            "w": args.w,
            "h": args.h,
        },
        "focused": args.focused,
        "z_order": "active" if args.focused else "background",
        "visible_text": args.visible_text,
        "control_tree_hash": args.control_tree_hash or "",
        "capture_ts": now_iso(),
    }
    previous_surface = load_previous_surface()
    if args.trust_status != "auto":
        event = build_surface_event(
            host=args.host,
            workspace=args.workspace,
            session=args.session,
            observer_id=args.observer_id,
            host_kind=args.host_kind,
            label=args.label,
            observation=observation,
            previous_surface=previous_surface,
        )
        event["payload"]["trust_state"] = {
            "status": args.trust_status,
            "drift_flags": args.drift_flags,
            "mismatch_flags": args.mismatch_flags,
        }
        return append_event(event)

    return append_surface_event(
        host=args.host,
        workspace=args.workspace,
        session=args.session,
        observer_id=args.observer_id,
        host_kind=args.host_kind,
        label=args.label,
        observation=observation,
        previous_surface=previous_surface,
    )


def ingest_ahk_logs() -> list[dict[str, Any]]:
    appended: list[dict[str, Any]] = []
    for path, event_type in ((AHK_LEARN_JSONL, "bridge.learn"), (AHK_RECORD_JSONL, "bridge.record")):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            clean = raw_line.strip()
            if not clean:
                continue
            item = json.loads(clean)
            event = {
                "type": event_type,
                "source": {
                    "host": "ahk-bridge",
                    "workspace": str(path.parent.parent.parent),
                    "session": "linux-local",
                    "observer": "ahk-v2",
                },
                "payload": item,
                "tags": ["bridge_imported"],
            }
            appended.append(append_event(event))
    return appended


def emit_web_event(args: argparse.Namespace) -> dict[str, Any]:
    previous_web = load_previous_web()
    candidate_surface = load_previous_surface()
    linked_surface = {
        "surface_id": args.linked_surface_id,
        "process_name": args.linked_process_name,
        "window_title": args.linked_window_title,
    }
    if args.trust_status != "auto":
        event = build_web_event(
            host=args.host,
            workspace=args.workspace,
            session=args.session,
            observer_id=args.observer_id,
            browser=args.browser,
            url=args.url,
            title=args.title,
            text_snippet=args.text_snippet,
            tab_id=args.tab_id,
            window_id=args.window_id,
            mutated=args.mutated,
            visible=not args.hidden,
            linked_surface=linked_surface,
            candidate_surface=candidate_surface,
            previous_web=previous_web,
        )
        event["payload"]["trust_state"] = {
            "status": args.trust_status,
            "drift_flags": args.drift_flags,
            "mismatch_flags": args.mismatch_flags,
        }
        return append_event(event)

    return append_web_event(
        host=args.host,
        workspace=args.workspace,
        session=args.session,
        observer_id=args.observer_id,
        browser=args.browser,
        url=args.url,
        title=args.title,
        text_snippet=args.text_snippet,
        tab_id=args.tab_id,
        window_id=args.window_id,
        mutated=args.mutated,
        visible=not args.hidden,
        linked_surface=linked_surface,
        candidate_surface=candidate_surface,
        previous_web=previous_web,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m bridges.alpha.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    append_cmd = sub.add_parser("append", help="Append an event from a file path or JSON string.")
    append_cmd.add_argument("event", help="JSON file path or raw JSON event")

    sub.add_parser("rebuild", help="Rebuild latest-state.json from events.jsonl")
    sub.add_parser("project", help="Project latest-tags.json and busydawg-state.json from state")
    cycle_cmd = sub.add_parser("cycle", help="Run rebuild + project")
    cycle_cmd.add_argument("--no-ahk-hook", action="store_true", help="Skip auto-publishing the latest policy hook")
    cycle_cmd.add_argument("--no-ahk-feedback", action="store_true", help="Skip auto-ingesting AHK feedback before rebuild")
    cycle_cmd.add_argument("--ahk-share-root", default="", help="Override the AHK shared sync root")
    cycle_cmd.add_argument("--ahk-hook-channel", default="ahk-policy", help="AHK hook channel name")
    cycle_cmd.add_argument("--ahk-feedback-channel", default="ahk-feedback", help="AHK feedback channel name")
    report_cmd = sub.add_parser("report", help="Print a short human-readable Alpha trust report")
    report_cmd.add_argument("--json", action="store_true", help="Print the report as JSON")
    validate_cmd = sub.add_parser("validate-browser", help="Run browser trust scenarios in memory")
    validate_cmd.add_argument("--dir", default=str(SCENARIOS_DIR), help="Scenario directory path")
    validate_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_mind_cmd = sub.add_parser("validate-mindseye", help="Run legacy AHK context correlation scenarios in memory")
    validate_mind_cmd.add_argument("--dir", default=str(MINDS_EYE_SCENARIOS_DIR), help="Scenario directory path")
    validate_mind_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_feedback_cmd = sub.add_parser("validate-ahk-feedback", help="Run AHK feedback scenarios in memory")
    validate_feedback_cmd.add_argument("--dir", default=str(AHK_FEEDBACK_SCENARIOS_DIR), help="Scenario directory path")
    validate_feedback_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_qtf_cmd = sub.add_parser("validate-qtf", help="Run QTF execution scenarios in memory")
    validate_qtf_cmd.add_argument("--dir", default=str(QTF_SCENARIOS_DIR), help="Scenario directory path")
    validate_qtf_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_host_cmd = sub.add_parser("validate-host-session", help="Run host session breadcrumb scenarios in memory")
    validate_host_cmd.add_argument("--dir", default=str(HOST_SESSION_SCENARIOS_DIR), help="Scenario directory path")
    validate_host_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_privilege_cmd = sub.add_parser("validate-privilege", help="Run privilege boundary scenarios in memory")
    validate_privilege_cmd.add_argument("--dir", default=str(PRIVILEGE_SCENARIOS_DIR), help="Scenario directory path")
    validate_privilege_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_ext_cmd = sub.add_parser("validate-ext", help="Run EXT promotion gate scenarios in memory")
    validate_ext_cmd.add_argument("--dir", default=str(EXT_SCENARIOS_DIR), help="Scenario directory path")
    validate_ext_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_package_cmd = sub.add_parser("validate-package", help="Run package install routing scenarios in memory")
    validate_package_cmd.add_argument("--dir", default=str(PACKAGE_SCENARIOS_DIR), help="Scenario directory path")
    validate_package_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_policy_cmd = sub.add_parser("validate-policy", help="Run policy scenarios in memory")
    validate_policy_cmd.add_argument("--dir", default=str(POLICY_SCENARIOS_DIR), help="Scenario directory path")
    validate_policy_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    validate_messy_cmd = sub.add_parser("validate-messy", help="Run full-chain messy scenarios in memory")
    validate_messy_cmd.add_argument("--dir", default=str(FULL_CHAIN_SCENARIOS_DIR), help="Scenario directory path")
    validate_messy_cmd.add_argument("--json", action="store_true", help="Print the full validation result as JSON")
    sub.add_parser("ingest-ahk", help="Import AHK bridge JSONL into the Alpha event bus")
    mindseye_cmd = sub.add_parser("ingest-mindseye", help="Import legacy AHK context shared sync events into Alpha")
    mindseye_cmd.add_argument("--share-root", default="", help="Shared sync root directory")
    mindseye_cmd.add_argument("--channel", default="mindseye", help="Shared sync channel name")
    mindseye_cmd.add_argument("--no-ahk-hook", action="store_true", help="Skip auto-publishing the latest policy hook")
    mindseye_cmd.add_argument("--no-ahk-feedback", action="store_true", help="Skip auto-ingesting AHK feedback after legacy AHK context import")
    mindseye_cmd.add_argument("--ahk-share-root", default="", help="Override the AHK shared sync root")
    mindseye_cmd.add_argument("--ahk-hook-channel", default="ahk-policy", help="AHK hook channel name")
    mindseye_cmd.add_argument("--ahk-feedback-channel", default="ahk-feedback", help="AHK feedback channel name")
    feedback_cmd = sub.add_parser("ingest-ahk-feedback", help="Import AHK feedback shared sync events into Alpha")
    feedback_cmd.add_argument("--share-root", default="", help="Shared sync root directory")
    feedback_cmd.add_argument("--channel", default="ahk-feedback", help="Shared sync channel name")
    feedback_cmd.add_argument("--no-ahk-hook", action="store_true", help="Skip auto-publishing the latest policy hook")
    feedback_cmd.add_argument("--ahk-share-root", default="", help="Override the AHK shared sync root")
    feedback_cmd.add_argument("--ahk-hook-channel", default="ahk-policy", help="AHK hook channel name")
    ahk_hook_cmd = sub.add_parser("publish-ahk-hook", help="Publish the latest policy decision to the AHK shared seam")
    ahk_hook_cmd.add_argument("--share-root", default="", help="Shared sync root directory")
    ahk_hook_cmd.add_argument("--channel", default="ahk-policy", help="Shared sync channel name")
    reset_cmd = sub.add_parser("reset-alpha", help="Clear generated Alpha runtime state")
    reset_cmd.add_argument("--archive", action="store_true", help="Archive current runtime files before reset")
    serve_cmd = sub.add_parser("serve-http", help="Run the local Alpha HTTP bridge")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=8765)
    qtf_cmd = sub.add_parser("qtf-run", help="Run a local/offline command inside the QTF cage")
    qtf_cmd.add_argument("--label", default="local-offline-cage", help="Human label for the QTF run")
    qtf_cmd.add_argument("--backend", choices=["auto", "bwrap", "podman"], default="auto", help="Containment backend")
    qtf_cmd.add_argument("--image", default="ubuntu:latest", help="Podman image to use when backend resolves to podman")
    qtf_cmd.add_argument("--workspace", default="", help="Local file or directory to copy into disposable /workspace")
    qtf_cmd.add_argument("--timeout", type=int, default=45, help="Execution timeout in seconds")
    qtf_cmd.add_argument("--keep-sandbox", action="store_true", help="Keep the disposable copied workspace on disk")
    qtf_cmd.add_argument("command", nargs=argparse.REMAINDER, help="Command to run after --")
    package_cmd = sub.add_parser("observe-package", help="Append one package.install.observe event and optionally route it into QTF")
    package_cmd.add_argument("--manager", choices=["npm", "pip", "apt", "flatpak", "snap", "custom"], default="npm")
    package_cmd.add_argument("--operation", default="install")
    package_cmd.add_argument("--package-name", default="")
    package_cmd.add_argument("--version-spec", default="")
    package_cmd.add_argument("--source-kind", choices=["local", "project", "registry", "custom"], default="local")
    package_cmd.add_argument("--workspace", default="", help="Local file or directory to copy into disposable /workspace when routing to QTF")
    package_cmd.add_argument("--scripts-policy", choices=["default", "ignore", "disabled"], default="default")
    package_cmd.add_argument("--lockfile-state", choices=["present", "missing", "unknown"], default="unknown")
    package_cmd.add_argument("--route-qtf", action="store_true", help="Run the observed command inside QTF immediately")
    package_cmd.add_argument("--qtf-label", default="", help="Override the QTF label used for routed execution")
    package_cmd.add_argument("--qtf-backend", choices=["auto", "bwrap", "podman"], default="auto")
    package_cmd.add_argument("--qtf-image", default="ubuntu:latest")
    package_cmd.add_argument("--timeout", type=int, default=45, help="Execution timeout in seconds")
    package_cmd.add_argument("command", nargs=argparse.REMAINDER, help="Observed command after --")
    host_cmd = sub.add_parser("observe-host-session", help="Append one host.session.observe breadcrumb and rebuild projections")
    host_cmd.add_argument("--stage", default="gnome-handoff", help="Session breadcrumb stage label")
    host_cmd.add_argument("--compromise-suspected", action="store_true", help="Mark this host session breadcrumb as suspicious")
    host_cmd.add_argument("--suspicion-note", default="", help="Optional operator note about why this session feels compromised")
    host_cmd.add_argument(
        "--recovery-hint",
        choices=["observe_only", "review", "recovery_ready", "lockdown_ready"],
        default="observe_only",
        help="Explicit recovery hint to surface through report/BusyDawg",
    )
    privilege_cmd = sub.add_parser("observe-privilege", help="Append one privilege.observe boundary event and rebuild projections")
    privilege_cmd.add_argument("--method", choices=["sudo", "su", "pkexec", "doas", "custom"], default="sudo")
    privilege_cmd.add_argument("--result", choices=["prompted", "granted", "denied", "failed"], default="prompted")
    privilege_cmd.add_argument("--target-user", default="root", help="Intended target user")
    privilege_cmd.add_argument("--target-uid", type=int, default=0, help="Intended target uid; use -1 to omit")
    privilege_cmd.add_argument("--reason", default="", help="Optional note about why this privilege boundary is being recorded")
    privilege_cmd.add_argument("command", nargs=argparse.REMAINDER, help="Observed command after --")
    ext_cmd = sub.add_parser("observe-ext", help="Append one ext.promotion.observe boundary event and rebuild projections")
    ext_cmd.add_argument("--result", choices=["requested", "denied", "withdrawn"], default="requested")
    ext_cmd.add_argument("--target", choices=["host", "workspace", "custom"], default="host")
    ext_cmd.add_argument("--artifact-kind", choices=["package", "workspace", "file", "custom"], default="package")
    ext_cmd.add_argument("--qtf-label", default="", help="QTF label this promotion request is tied to")
    ext_cmd.add_argument("--package-name", default="", help="Optional package name for the promotion request")
    ext_cmd.add_argument("--package-manager", default="", help="Optional package manager for the promotion request")
    ext_cmd.add_argument("--reason", default="", help="Optional note about why this promotion boundary is being recorded")

    surface_cmd = sub.add_parser("emit-surface", help="Append one surface.observe event")
    surface_cmd.add_argument("--host", default="linux-spy")
    surface_cmd.add_argument("--workspace", default=str(Path.cwd()))
    surface_cmd.add_argument("--session", default="default")
    surface_cmd.add_argument("--observer-id", default="window-spy-linux")
    surface_cmd.add_argument("--host-kind", default="desktop")
    surface_cmd.add_argument("--label", default="active_surface")
    surface_cmd.add_argument("--platform", default="linux-x11")
    surface_cmd.add_argument("--surface-id", required=True)
    surface_cmd.add_argument("--pid", type=int, default=0)
    surface_cmd.add_argument("--process-name", default="")
    surface_cmd.add_argument("--process-path", default="")
    surface_cmd.add_argument("--window-class", default="")
    surface_cmd.add_argument("--window-title", default="")
    surface_cmd.add_argument("--x", type=int, default=0)
    surface_cmd.add_argument("--y", type=int, default=0)
    surface_cmd.add_argument("--w", type=int, default=0)
    surface_cmd.add_argument("--h", type=int, default=0)
    surface_cmd.add_argument("--visible-text", default="")
    surface_cmd.add_argument("--control-tree-hash", default="")
    surface_cmd.add_argument("--focused", action="store_true")
    surface_cmd.add_argument(
        "--trust-status",
        choices=["auto", "trusted", "shifted", "suspicious", "unknown"],
        default="auto",
    )
    surface_cmd.add_argument("--drift-flags", nargs="*", default=[])
    surface_cmd.add_argument("--mismatch-flags", nargs="*", default=[])

    web_cmd = sub.add_parser("emit-web", help="Append one web.observe event")
    web_cmd.add_argument("--host", default="browser-observer")
    web_cmd.add_argument("--workspace", default=str(Path.cwd()))
    web_cmd.add_argument("--session", default="browser-active")
    web_cmd.add_argument("--observer-id", default="chrome-extension")
    web_cmd.add_argument("--browser", default="chrome")
    web_cmd.add_argument("--url", required=True)
    web_cmd.add_argument("--title", default="")
    web_cmd.add_argument("--text-snippet", default="")
    web_cmd.add_argument("--tab-id", type=int, default=0)
    web_cmd.add_argument("--window-id", type=int, default=0)
    web_cmd.add_argument("--mutated", action="store_true")
    web_cmd.add_argument("--hidden", action="store_true")
    web_cmd.add_argument("--linked-surface-id", default="")
    web_cmd.add_argument("--linked-process-name", default="")
    web_cmd.add_argument("--linked-window-title", default="")
    web_cmd.add_argument(
        "--trust-status",
        choices=["auto", "trusted", "shifted", "suspicious", "unknown"],
        default="auto",
    )
    web_cmd.add_argument("--drift-flags", nargs="*", default=[])
    web_cmd.add_argument("--mismatch-flags", nargs="*", default=[])

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.cmd == "append":
        event = append_event(_load_json_arg(args.event))
        print(dump_json(event))
        return 0

    if args.cmd == "rebuild":
        state = rebuild_state()
        print(dump_json(state))
        return 0

    if args.cmd == "project":
        tags = project_tags()
        projection = project_busydawg()
        print(dump_json({"tags": tags, "busydawg": projection}))
        return 0

    if args.cmd == "cycle":
        feedback_result = ingest_ahk_feedback_events(
            share_root=args.ahk_share_root or None,
            channel=args.ahk_feedback_channel,
        ) if not args.no_ahk_feedback else None
        state = rebuild_state()
        tags = project_tags()
        projection = project_busydawg()
        ahk_hook = _maybe_publish_ahk_hook(
            state=state,
            tags=tags,
            projection=projection,
            enabled=not args.no_ahk_hook,
            share_root=args.ahk_share_root or None,
            channel=args.ahk_hook_channel,
        )
        print(
            dump_json(
                {
                    "events_path": str(EVENTS_JSONL),
                    "state_path": str(LATEST_STATE_JSON),
                    "tags_path": str(LATEST_TAGS_JSON),
                    "busydawg_path": str(BUSYDAWG_STATE_JSON),
                    "event_count": state.get("event_count", 0),
                    "trust_status": tags.get("trust_status"),
                    "ahk_feedback": feedback_result,
                    "ahk_hook": ahk_hook,
                }
            )
        )
        return 0

    if args.cmd == "report":
        state = rebuild_state()
        tags = project_tags()
        projection = project_busydawg()
        report = build_report_payload(state, tags, projection)
        if args.json:
            print(dump_report_json(report))
        else:
            print(render_report_text(report))
        return 0

    if args.cmd == "validate-browser":
        result = validate_browser_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Browser trust validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(f"  Summary: {item['actual'].get('summary', '')}")
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-mindseye":
        result = validate_mindseye_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"AHK context correlation validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(f"  Summary: {item['actual'].get('summary', '')}")
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-ahk-feedback":
        result = validate_ahk_feedback_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"AHK feedback validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Response: {item['actual'].get('user_response', '')} | "
                    f"Hot node: {item['actual'].get('hot_node', '')}"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-qtf":
        result = validate_qtf_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"QTF validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Backend: {item['actual'].get('qtf_backend', '')} | "
                    f"Success: {item['actual'].get('qtf_success', '')}"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-host-session":
        result = validate_host_session_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Host session validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Stage: {item['actual'].get('stage', '')} | "
                    f"Recovery: {item['actual'].get('recovery_hint', '')} | "
                    f"Hot node: {item['actual'].get('hot_node', '')}"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-privilege":
        result = validate_privilege_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Privilege validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Method: {item['actual'].get('method', '')} | "
                    f"Result: {item['actual'].get('result', '')} | "
                    f"Policy: {item['actual'].get('policy_action', '')} ({item['actual'].get('policy_rule', '')})"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-ext":
        result = validate_ext_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"EXT validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Result: {item['actual'].get('result', '')} | "
                    f"Target: {item['actual'].get('target', '')} | "
                    f"Policy: {item['actual'].get('policy_action', '')} ({item['actual'].get('policy_rule', '')})"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-package":
        result = validate_package_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Package validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Manager: {item['actual'].get('package_manager', '')} | "
                    f"QTF: {item['actual'].get('qtf_backend', '')} / {item['actual'].get('qtf_success', '')} | "
                    f"Policy: {item['actual'].get('policy_action', '')} ({item['actual'].get('policy_rule', '')})"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-policy":
        result = validate_policy_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Policy validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(f"  Action: {item['actual'].get('policy_action', '')}")
                print(f"  Rule: {item['actual'].get('policy_rule', '')}")
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "validate-messy":
        result = validate_full_chain_scenarios(Path(args.dir))
        if args.json:
            print(dump_json(result))
        else:
            print(
                f"Full-chain messy validation: {result['passed']}/{result['scenario_count']} passed "
                f"({result['failed']} failed)"
            )
            for item in result["results"]:
                status = "PASS" if item["passed"] else "FAIL"
                print(f"[{status}] {item['name']} ({item['id']})")
                print(
                    f"  Trust: {item['actual'].get('overall_trust', '')} | "
                    f"Policy: {item['actual'].get('policy_action', '')} ({item['actual'].get('policy_rule', '')})"
                )
                if item["failures"]:
                    for failure in item["failures"]:
                        print(f"  - {failure}")
        return 0 if result["failed"] == 0 else 1

    if args.cmd == "reset-alpha":
        print(dump_json(reset_alpha(archive=args.archive)))
        return 0

    if args.cmd == "ingest-mindseye":
        result = ingest_mindseye_and_cycle(share_root=args.share_root or None, channel=args.channel)
        feedback_result = None
        if result.get("status") != "missing" and not args.no_ahk_feedback:
            feedback_result = ingest_ahk_feedback_events(
                share_root=args.ahk_share_root or None,
                channel=args.ahk_feedback_channel,
            )
            result["state"] = rebuild_state()
            result["tags"] = project_tags()
            result["busydawg"] = project_busydawg()
        result["ahk_feedback"] = feedback_result
        if result.get("status") != "missing" and result.get("state") and result.get("tags") and result.get("busydawg"):
            result["ahk_hook"] = _maybe_publish_ahk_hook(
                state=result["state"],
                tags=result["tags"],
                projection=result["busydawg"],
                enabled=not args.no_ahk_hook,
                share_root=args.ahk_share_root or None,
                channel=args.ahk_hook_channel,
            )
        else:
            result["ahk_hook"] = None
        print(dump_json(result))
        return 0

    if args.cmd == "ingest-ahk-feedback":
        result = ingest_ahk_feedback_and_cycle(share_root=args.share_root or None, channel=args.channel)
        if result.get("status") != "missing" and result.get("state") and result.get("tags") and result.get("busydawg"):
            result["ahk_hook"] = _maybe_publish_ahk_hook(
                state=result["state"],
                tags=result["tags"],
                projection=result["busydawg"],
                enabled=not args.no_ahk_hook,
                share_root=args.ahk_share_root or None,
                channel=args.ahk_hook_channel,
            )
        else:
            result["ahk_hook"] = None
        print(dump_json(result))
        return 0

    if args.cmd == "publish-ahk-hook":
        state = rebuild_state()
        tags = project_tags()
        projection = project_busydawg()
        report = build_report_payload(state, tags, projection)
        result = publish_ahk_policy_hook(report, share_root=args.share_root or None, channel=args.channel)
        print(dump_json(result))
        return 0

    if args.cmd == "qtf-run":
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            parser.error("qtf-run requires a command after --")

        result = run_qtf_command(
            command=command,
            label=args.label,
            backend=args.backend,
            image=args.image,
            workspace=args.workspace or None,
            timeout_seconds=args.timeout,
            keep_sandbox=args.keep_sandbox,
        )
        if result.get("status") != "executed":
            print(dump_json(result))
            return 1

        state = rebuild_state()
        tags = project_tags()
        projection = project_busydawg()
        report = build_report_payload(state, tags, projection)
        result["report"] = {
            "overall_status": report.get("overall_status"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "active_qtf_execution": report.get("active_qtf_execution"),
            "paths": report.get("paths"),
        }
        print(dump_json(result))
        return 0

    if args.cmd == "observe-package":
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]

        result = observe_package_install(
            manager=args.manager,
            operation=args.operation,
            package_name=args.package_name,
            version_spec=args.version_spec,
            source_kind=args.source_kind,
            workspace=args.workspace or None,
            command=command,
            scripts_policy=args.scripts_policy,
            lockfile_state=args.lockfile_state,
            route_qtf=args.route_qtf,
            qtf_label=args.qtf_label,
            qtf_backend=args.qtf_backend,
            qtf_image=args.qtf_image,
            timeout_seconds=args.timeout,
        )
        if result.get("status") == "error":
            print(dump_json(result))
            return 1

        state = rebuild_state()
        tags = project_tags()
        projection = project_busydawg()
        report = build_report_payload(state, tags, projection)
        result["report"] = {
            "overall_status": report.get("overall_status"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "active_package_install": report.get("active_package_install"),
            "active_qtf_execution": report.get("active_qtf_execution"),
            "paths": report.get("paths"),
        }
        print(dump_json(result))
        return 0

    if args.cmd == "observe-host-session":
        result = observe_host_session_and_cycle(
            stage=args.stage,
            compromise_suspected=args.compromise_suspected,
            suspicion_note=args.suspicion_note,
            recovery_hint=args.recovery_hint,
        )
        report = build_report_payload(result["state"], result["tags"], result["busydawg"])
        result["report"] = {
            "overall_status": report.get("overall_status"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "active_host_session": report.get("active_host_session"),
            "paths": report.get("paths"),
        }
        print(dump_json(result))
        return 0

    if args.cmd == "observe-privilege":
        command = list(args.command)
        if command and command[0] == "--":
            command = command[1:]
        result = observe_privilege_and_cycle(
            method=args.method,
            result=args.result,
            target_user=args.target_user,
            target_uid=(None if args.target_uid < 0 else args.target_uid),
            reason=args.reason,
            command=command,
        )
        report = build_report_payload(result["state"], result["tags"], result["busydawg"])
        result["report"] = {
            "overall_status": report.get("overall_status"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "active_privilege": report.get("active_privilege"),
            "paths": report.get("paths"),
        }
        print(dump_json(result))
        return 0

    if args.cmd == "observe-ext":
        result = observe_ext_and_cycle(
            result=args.result,
            target=args.target,
            artifact_kind=args.artifact_kind,
            qtf_label=args.qtf_label,
            package_name=args.package_name,
            package_manager=args.package_manager,
            reason=args.reason,
        )
        report = build_report_payload(result["state"], result["tags"], result["busydawg"])
        result["report"] = {
            "overall_status": report.get("overall_status"),
            "policy_action": (report.get("policy") or {}).get("action"),
            "active_ext_promotion": report.get("active_ext_promotion"),
            "paths": report.get("paths"),
        }
        print(dump_json(result))
        return 0

    if args.cmd == "serve-http":
        serve_http_bridge(host=args.host, port=args.port)
        return 0

    if args.cmd == "emit-surface":
        print(dump_json(emit_surface_event(args)))
        return 0

    if args.cmd == "emit-web":
        print(dump_json(emit_web_event(args)))
        return 0

    if args.cmd == "ingest-ahk":
        appended = ingest_ahk_logs()
        print(dump_json({"imported": len(appended)}))
        return 0

    parser.error("Unknown command.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
