from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

from .models import now_iso
from .paths import PROJECT_ROOT, SPAWN_STATE_JSON, STATE_DIR


LANE_CATALOG: list[dict[str, Any]] = [
    {
        "id": "codex_local",
        "label": "Codex 5.4",
        "kind": "local",
        "provider": "codex",
        "default_model": "gpt-5.4",
        "model_options": ["gpt-5.4", "gpt-5.4-mini"],
        "tagline": "Local Codex lane for direct repo-aware execution.",
        "copy_hint": "Automated locally through codex exec.",
    },
    {
        "id": "claude_code",
        "label": "Claude Code",
        "kind": "local",
        "provider": "claude",
        "default_model": "qwen3.5",
        "model_options": ["qwen3.5", "sonnet", "opus"],
        "tagline": "Governed local Claude lane with cheap-mode defaults.",
        "copy_hint": "Automated locally through the governed Claude wrapper.",
    },
    {
        "id": "web_gpt",
        "label": "Web GPT",
        "kind": "manual",
        "provider": "manual",
        "default_model": "manual",
        "model_options": ["manual"],
        "tagline": "Paste browser-chat output here after running the generated prompt.",
        "copy_hint": "Copy the generated prompt into your browser chat, then paste the reply back here.",
    },
    {
        "id": "claude_web",
        "label": "Claude Web",
        "kind": "manual",
        "provider": "manual",
        "default_model": "manual",
        "model_options": ["manual"],
        "tagline": "Use this for the full Claude web/app lane when you want the heavier model.",
        "copy_hint": "Copy the generated prompt into Claude web/app, then paste the answer back here.",
    },
]

RUBRIC: list[dict[str, str]] = [
    {"id": "clarity", "label": "Clarity"},
    {"id": "feasibility", "label": "Feasibility"},
    {"id": "risk_honesty", "label": "Risk Honesty"},
    {"id": "novelty", "label": "Novelty"},
]


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
            "provider": "codex",
            "model": "gpt-5.4",
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
            "judge_options": [
                {"provider": "codex", "label": "Codex Judge", "model_options": ["gpt-5.4", "gpt-5.4-mini"]},
                {"provider": "claude", "label": "Claude Judge", "model_options": ["qwen3.5", "sonnet", "opus"]},
            ],
        },
        "guidance": {
            "seed": "Fan one shared prompt into multiple lanes and let them answer independently.",
            "cross": "Then make each lane inspect the others instead of protecting its first answer.",
            "foldback": "Use a final judge prompt to score the disagreement and recommend the next move.",
        },
    }


def _run_claude(prompt: str, model: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["CLAUDE_MODEL_OVERRIDE"] = model or "qwen3.5"
    command = [str(PROJECT_ROOT / "scripts" / "claude-quick.sh"), prompt]
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=240,
        check=False,
    )
    response = (completed.stdout or "").strip()
    return {
        "ok": completed.returncode == 0 and bool(response),
        "provider": "claude",
        "model": env["CLAUDE_MODEL_OVERRIDE"],
        "prompt": prompt,
        "response": response,
        "stdout": completed.stdout if completed.returncode != 0 else "",
        "stderr": completed.stderr if completed.returncode != 0 else "",
        "returncode": completed.returncode,
        "duration_ms": int((time.monotonic() - started) * 1000),
        "ts": now_iso(),
    }


def _run_codex(prompt: str, model: str) -> dict[str, Any]:
    output_path = None
    started = time.monotonic()
    try:
        with tempfile.NamedTemporaryFile(prefix="spawn-codex-", suffix=".txt", delete=False) as handle:
            output_path = Path(handle.name)

        command = [
            "codex",
            "exec",
            "-C",
            str(PROJECT_ROOT),
            "--sandbox",
            "danger-full-access",
            "--color",
            "never",
            "-m",
            model or "gpt-5.4",
            "-o",
            str(output_path),
            prompt,
        ]

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
            "provider": "codex",
            "model": model or "gpt-5.4",
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

    if provider == "claude":
        return _run_claude(prompt, model)
    if provider == "codex":
        return _run_codex(prompt, model)

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
