#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
GUIDANCE="$(cat "$ROOT/CLAUDE.md")"
MODEL="${CLAUDE_MODEL_OVERRIDE:-qwen3.5}"

export CLAUDE_CODE_NO_FLICKER=1

exec claude \
  --bare \
  --add-dir "$ROOT" \
  --append-system-prompt "$GUIDANCE" \
  --model "$MODEL" \
  --effort low \
  --permission-mode default \
  -n "QTMoS Governed" \
  "$@"
