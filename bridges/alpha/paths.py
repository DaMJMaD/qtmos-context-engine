from __future__ import annotations

from pathlib import Path


ALPHA_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ALPHA_DIR.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
RUNTIME_DIR = PROJECT_ROOT / "runtime"
BUS_DIR = RUNTIME_DIR / "bus"
STATE_DIR = RUNTIME_DIR / "state"
TAGS_DIR = RUNTIME_DIR / "tags"
INGEST_DIR = RUNTIME_DIR / "ingest"

EVENTS_JSONL = BUS_DIR / "events.jsonl"
LATEST_STATE_JSON = STATE_DIR / "latest-state.json"
LATEST_TAGS_JSON = TAGS_DIR / "latest-tags.json"
BUSYDAWG_STATE_JSON = STATE_DIR / "busydawg-state.json"
SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "browser-trust"
MINDS_EYE_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "mindseye-correlation"
POLICY_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "policy"
FULL_CHAIN_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "full-chain-messy"
AHK_FEEDBACK_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "ahk-feedback"
QTF_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "qtf"
PACKAGE_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "package"
HOST_SESSION_SCENARIOS_DIR = PROJECT_ROOT / "scenarios" / "host-session"
MINDS_EYE_CURSOR_JSON = INGEST_DIR / "mindseye-cursor.json"
AHK_FEEDBACK_CURSOR_JSON = INGEST_DIR / "ahk-feedback-cursor.json"
POLICY_RULES_JSON = CONFIG_DIR / "policy_rules.json"

AHK_BRIDGE_DIR = PROJECT_ROOT / "bridges" / "ahk-v2" / "data"
AHK_LEARN_JSONL = AHK_BRIDGE_DIR / "learn.jsonl"
AHK_RECORD_JSONL = AHK_BRIDGE_DIR / "record.jsonl"


def ensure_runtime_dirs() -> None:
    for path in (BUS_DIR, STATE_DIR, TAGS_DIR, INGEST_DIR):
        path.mkdir(parents=True, exist_ok=True)
