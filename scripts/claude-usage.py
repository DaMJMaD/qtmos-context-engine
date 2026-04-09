#!/usr/bin/env python3
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys


@dataclass
class SessionSummary:
    path: Path
    session_id: str
    updated_at: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    turns: int = 0
    last_prompt: str = ""


def project_dir() -> Path:
    repo_root = Path(__file__).resolve().parents[1]
    slug = "-" + str(repo_root).strip("/").replace("/", "-").replace(" ", "-")
    return Path.home() / ".claude" / "projects" / slug


def parse_session(path: Path) -> SessionSummary:
    summary = SessionSummary(path=path, session_id=path.stem)

    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue

            try:
                record = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            timestamp = record.get("timestamp")
            if timestamp:
                summary.updated_at = timestamp

            if record.get("type") == "last-prompt":
                summary.last_prompt = record.get("lastPrompt", "")
                continue

            if record.get("type") != "assistant":
                continue

            message = record.get("message", {})
            usage = message.get("usage", {})
            summary.input_tokens += int(usage.get("input_tokens", 0) or 0)
            summary.output_tokens += int(usage.get("output_tokens", 0) or 0)
            summary.turns += 1

    return summary


def sort_key(summary: SessionSummary) -> tuple[int, str]:
    if not summary.updated_at:
        return (0, summary.session_id)
    try:
        dt = datetime.fromisoformat(summary.updated_at.replace("Z", "+00:00"))
    except ValueError:
        return (0, summary.updated_at)
    return (int(dt.timestamp()), summary.updated_at)


def shorten(text: str, limit: int = 72) -> str:
    clean = " ".join(text.split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 3] + "..."


def main() -> int:
    limit = 5
    if len(sys.argv) > 1:
        try:
            limit = max(1, int(sys.argv[1]))
        except ValueError:
            print("usage: ./scripts/claude-usage.py [count]", file=sys.stderr)
            return 2

    directory = project_dir()
    if not directory.exists():
        print("No Claude project history found for this repo yet.")
        return 0

    sessions = [parse_session(path) for path in directory.glob("*.jsonl")]
    sessions = [session for session in sessions if session.turns or session.last_prompt]
    sessions.sort(key=sort_key, reverse=True)

    if not sessions:
        print("No Claude sessions with usage data found for this repo yet.")
        return 0

    recent = sessions[:limit]
    total_input = sum(session.input_tokens for session in recent)
    total_output = sum(session.output_tokens for session in recent)

    print(f"Claude usage for {directory.name} (latest {len(recent)} session(s))")
    print(f"input tokens:  {total_input}")
    print(f"output tokens: {total_output}")
    print("")

    for session in recent:
        updated = session.updated_at or "unknown-time"
        print(
            f"- {updated} | in {session.input_tokens} | out {session.output_tokens} | turns {session.turns}"
        )
        if session.last_prompt:
            print(f"  prompt: {shorten(session.last_prompt)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
