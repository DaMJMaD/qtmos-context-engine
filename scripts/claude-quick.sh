#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
GUIDANCE="$(cat "$ROOT/CLAUDE.md")"
MODEL="${CLAUDE_MODEL_OVERRIDE:-qwen3.5}"
export CLAUDE_CODE_NO_FLICKER=1

if [[ $# -eq 0 ]]; then
  echo "Usage: ./scripts/claude-quick.sh \"your prompt\"" >&2
  exit 1
fi

exec claude \
  --bare \
  --add-dir "$ROOT" \
  --append-system-prompt "$GUIDANCE" \
  --model "$MODEL" \
  --effort low \
  --permission-mode default \
  --max-budget-usd 0.25 \
  -p \
  "$@"
