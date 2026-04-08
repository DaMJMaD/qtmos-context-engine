from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any


REQUIRED_FIELDS = ("type", "source", "payload")


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_event(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict):
        raise TypeError("Event must be an object.")

    missing = [field for field in REQUIRED_FIELDS if field not in raw]
    if missing:
        raise ValueError(f"Missing required event fields: {', '.join(missing)}")

    event = dict(raw)
    event.setdefault("id", f"evt_{uuid.uuid4().hex[:12]}")
    event.setdefault("ts", now_iso())

    if not isinstance(event["type"], str) or not event["type"].strip():
        raise ValueError("Event type must be a non-empty string.")

    if not isinstance(event["source"], dict):
        raise ValueError("Event source must be an object.")

    if not isinstance(event["payload"], dict):
        raise ValueError("Event payload must be an object.")

    event.setdefault("rails", {})
    event.setdefault("tags", [])

    if not isinstance(event["rails"], dict):
        raise ValueError("Event rails must be an object.")

    if not isinstance(event["tags"], list):
        raise ValueError("Event tags must be a list.")

    source = dict(event["source"])
    source.setdefault("host", "unknown")
    source.setdefault("session", "default")
    event["source"] = source

    return event


def dump_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)

