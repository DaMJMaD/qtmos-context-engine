from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import normalize_event
from .paths import EVENTS_JSONL, ensure_runtime_dirs


def append_event(raw: dict[str, Any], event_path: Path = EVENTS_JSONL) -> dict[str, Any]:
    ensure_runtime_dirs()
    event = normalize_event(raw)
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def load_events(event_path: Path = EVENTS_JSONL) -> list[dict[str, Any]]:
    if not event_path.exists():
        return []

    events: list[dict[str, Any]] = []
    with event_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            clean = line.strip()
            if not clean:
                continue
            events.append(json.loads(clean))
    return events

