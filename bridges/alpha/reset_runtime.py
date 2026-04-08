from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .paths import (
    BUSYDAWG_STATE_JSON,
    EVENTS_JSONL,
    LATEST_STATE_JSON,
    LATEST_TAGS_JSON,
    MINDS_EYE_CURSOR_JSON,
    RUNTIME_DIR,
    ensure_runtime_dirs,
)


GENERATED_FILES = (
    EVENTS_JSONL,
    LATEST_STATE_JSON,
    LATEST_TAGS_JSON,
    BUSYDAWG_STATE_JSON,
    MINDS_EYE_CURSOR_JSON,
)


def _archive_runtime_files(archive_root: Path) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = archive_root / timestamp
    archive_dir.mkdir(parents=True, exist_ok=True)

    archived: dict[str, str] = {}
    for path in GENERATED_FILES:
        if not path.exists():
            continue
        target = archive_dir / path.relative_to(RUNTIME_DIR)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        archived[str(path)] = str(target)
    return archived


def reset_alpha(*, archive: bool = False) -> dict[str, object]:
    ensure_runtime_dirs()

    archived: dict[str, str] = {}
    if archive:
        archived = _archive_runtime_files(RUNTIME_DIR / "archive")

    removed: list[str] = []
    events_cleared = False

    if EVENTS_JSONL.exists():
        EVENTS_JSONL.write_text("", encoding="utf-8")
        events_cleared = True
    else:
        EVENTS_JSONL.touch()
        events_cleared = True
    removed.append(str(EVENTS_JSONL))

    for path in (LATEST_STATE_JSON, LATEST_TAGS_JSON, BUSYDAWG_STATE_JSON, MINDS_EYE_CURSOR_JSON):
        if path.exists():
            path.unlink()
            removed.append(str(path))

    return {
        "status": "reset",
        "events_cleared": events_cleared,
        "removed": removed,
        "archived": archived,
        "runtime_root": str(RUNTIME_DIR),
    }
