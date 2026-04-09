from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .models import now_iso
from .paths import PROJECT_ROOT, SPAWN_STATE_JSON, STATE_DIR


DEFAULT_MODEL_PROFILE = "balanced"
MODEL_PROFILES = ["balanced", "fast"]


LANE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "local_runtime",
        "label": "Local Runtime",
        "kind": "local",
        "provider": "local",
        "default_model": DEFAULT_MODEL_PROFILE,
        "model_options": MODEL_PROFILES,
        "tagline": "Local execution lane for direct repo-aware work.",
        "copy_hint": "Automated locally through your configured runtime command.",
    },
    {
        "id": "browser_witness",
        "label": "Browser Witness",
        "kind": "manual",
        "provider": "manual",
        "default_model": "manual",
        "model_options": ["manual"],
        "tagline": "Paste browser-side output here after running the generated prompt.",
        "copy_hint": "Copy the generated prompt into your browser model, then paste the reply back here.",
    },
]

RUBRIC: list[dict[str, str]] = [
    {"id": "clarity", "label": "Clarity"},
    {"id": "feasibility", "label": "Feasibility"},
    {"id": "risk_honesty", "label": "Risk Honesty"},
    {"id": "novelty", "label": "Novelty"},
]

JUDGE_OPTIONS: list[dict[str, Any]] = [
    {"provider": "local", "label": "Local Judge", "model_options": MODEL_PROFILES},
]


def _judge_option(provider: str) -> dict[str, Any] | None:
    for item in JUDGE_OPTIONS:
        if item["provider"] == provider:
            return item
    return None


def _lane_defaults() -> dict[str, dict[str, Any]]:
    return {
        lane["id"]: {
            "id": lane["id"],
            "label": lane["label"],
            "kind": lane["kind"],
            "provider": lane["provider"],
            "model": lane["default_model"],
            "seed_prompt": "",
            "seed_response": "",
            "cross_prompt": "",
            "cross_response": "",
            "notes": "",
            "status": "idle",
            "last_error": "",
            "updated_at": None,
        }
        for lane in LANE_CATALOG
    }


def default_spawn_workspace() -> dict[str, Any]:
    return {
        "session_name": "Spawn Workspace",
        "shared_prompt": "",
        "notes": "",
        "formula": "2×1×2",
        "focus": "Duality spark -> cross-exam -> total foldback",
        "lanes": _lane_defaults(),
        "judge": {
            "provider": "local",
            "model": DEFAULT_MODEL_PROFILE,
            "prompt": "",
            "response": "",
            "status": "idle",
            "last_error": "",
            "updated_at": None,
        },
        "updated_at": now_iso(),
    }


def _sanitize_lane(raw: Any, defaults: dict[str, Any]) -> dict[str, Any]:
    lane = dict(defaults)
    if not isinstance(raw, dict):
        return lane

    for key in ("model", "seed_prompt", "seed_response", "cross_prompt", "cross_response", "notes", "status", "last_error"):
        value = raw.get(key)
        if isinstance(value, str):
            lane[key] = value

    updated_at = raw.get("updated_at")
    if isinstance(updated_at, str):
        lane["updated_at"] = updated_at

    return lane


def sanitize_spawn_workspace(raw: Any) -> dict[str, Any]:
    defaults = default_spawn_workspace()
    if not isinstance(raw, dict):
        return defaults

    workspace = dict(defaults)
    for key in ("session_name", "shared_prompt", "notes", "formula", "focus"):
        value = raw.get(key)
        if isinstance(value, str):
            workspace[key] = value

    if isinstance(raw.get("judge"), dict):
        judge = dict(workspace["judge"])
        raw_judge = raw["judge"]
        for key in ("provider", "model", "prompt", "response", "status", "last_error"):
            value = raw_judge.get(key)
            if isinstance(value, str):
                judge[key] = value
        updated_at = raw_judge.get("updated_at")
        if isinstance(updated_at, str):
            judge["updated_at"] = updated_at
        option = _judge_option(judge["provider"])
        if option is None:
            judge["provider"] = defaults["judge"]["provider"]
            judge["model"] = defaults["judge"]["model"]
        elif judge["model"] not in option["model_options"]:
            judge["model"] = option["model_options"][0]
        workspace["judge"] = judge

    raw_lanes = raw.get("lanes")
    if isinstance(raw_lanes, dict):
        for lane_id, lane_defaults in defaults["lanes"].items():
            workspace["lanes"][lane_id] = _sanitize_lane(raw_lanes.get(lane_id), lane_defaults)

    updated_at = raw.get("updated_at")
    if isinstance(updated_at, str):
        workspace["updated_at"] = updated_at

    return workspace


def load_spawn_workspace() -> dict[str, Any]:
    if not SPAWN_STATE_JSON.exists():
        return default_spawn_workspace()
    try:
        raw = json.loads(SPAWN_STATE_JSON.read_text(encoding="utf-8"))
    except Exception:
        return default_spawn_workspace()
    return sanitize_spawn_workspace(raw)


def save_spawn_workspace(raw: Any) -> dict[str, Any]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    workspace = sanitize_spawn_workspace(raw)
    workspace["updated_at"] = now_iso()
    SPAWN_STATE_JSON.write_text(json.dumps(workspace, indent=2, sort_keys=True), encoding="utf-8")
    return workspace


def reset_spawn_workspace() -> dict[str, Any]:
    workspace = default_spawn_workspace()
    return save_spawn_workspace(workspace)


def build_spawn_payload() -> dict[str, Any]:
    return {
        "status": "ok",
        "workspace": load_spawn_workspace(),
        "catalog": {
            "lanes": LANE_CATALOG,
            "rubric": RUBRIC,
            "judge_options": JUDGE_OPTIONS,
        },
        "guidance": {
            "seed": "Fan one shared prompt into multiple lanes and let them answer independently.",
            "cross": "Then make each lane inspect the others instead of protecting its first answer.",
            "foldback": "Use a final judge prompt to score the disagreement and recommend the next move.",
        },
    }


def _resolve_local_model(profile: str) -> str:
    normalized = (profile or DEFAULT_MODEL_PROFILE).strip().lower() or DEFAULT_MODEL_PROFILE
    if normalized == "fast":
        return os.environ.get("QTMOS_SPAWN_MODEL_FAST", "fast")
    return os.environ.get("QTMOS_SPAWN_MODEL_BALANCED", "balanced")


def _run_local_runtime(prompt: str, model: str) -> dict[str, Any]:
    configured_command = os.environ.get("QTMOS_SPAWN_LOCAL_COMMAND", "").strip()
    if not configured_command:
        return {
            "ok": False,
            "provider": "local",
            "model": model or DEFAULT_MODEL_PROFILE,
            "prompt": prompt,
            "response": "",
            "stdout": "",
            "stderr": "Set QTMOS_SPAWN_LOCAL_COMMAND to automate the local lane.",
            "returncode": 1,
            "duration_ms": 0,
            "ts": now_iso(),
        }

    output_path = None
    prompt_path = None
    started = time.monotonic()
    try:
        with tempfile.NamedTemporaryFile(prefix="spawn-local-output-", suffix=".txt", delete=False) as handle:
            output_path = Path(handle.name)
        with tempfile.NamedTemporaryFile(prefix="spawn-local-prompt-", suffix=".txt", mode="w", encoding="utf-8", delete=False) as handle:
            handle.write(prompt)
            prompt_path = Path(handle.name)

        resolved_model = _resolve_local_model(model)
        command = shlex.split(
            configured_command.format(
                project_root=str(PROJECT_ROOT),
                model=resolved_model,
                output_path=str(output_path),
                prompt_path=str(prompt_path),
            )
        )

        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
        response = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
        return {
            "ok": completed.returncode == 0 and bool(response),
            "provider": "local",
            "model": model or DEFAULT_MODEL_PROFILE,
            "prompt": prompt,
            "response": response,
            "stdout": completed.stdout if completed.returncode != 0 else "",
            "stderr": completed.stderr if completed.returncode != 0 else "",
            "returncode": completed.returncode,
            "duration_ms": int((time.monotonic() - started) * 1000),
            "ts": now_iso(),
        }
    finally:
        if output_path and output_path.exists():
            try:
                output_path.unlink()
            except OSError:
                pass
        if prompt_path and prompt_path.exists():
            try:
                prompt_path.unlink()
            except OSError:
                pass


def invoke_spawn_provider(*, provider: str, prompt: str, model: str = "") -> dict[str, Any]:
    prompt = (prompt or "").strip()
    if not prompt:
        return {
            "ok": False,
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "response": "",
            "stdout": "",
            "stderr": "Prompt was empty.",
            "returncode": 1,
            "duration_ms": 0,
            "ts": now_iso(),
        }

    if provider == "local":
        return _run_local_runtime(prompt, model)

    return {
        "ok": False,
        "provider": provider,
        "model": model,
        "prompt": prompt,
        "response": "",
        "stdout": "",
        "stderr": f"Unknown provider: {provider}",
        "returncode": 1,
        "duration_ms": 0,
        "ts": now_iso(),
    }
