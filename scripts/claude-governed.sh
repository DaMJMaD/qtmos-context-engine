#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
GUIDANCE="$(cat "$ROOT/CLAUDE.md")"

exec claude \
  --bare \
  --add-dir "$ROOT" \
  --append-system-prompt "$GUIDANCE" \
  --effort low \
  --permission-mode default \
  -n "QTMoS Governed" \
  "$@"
