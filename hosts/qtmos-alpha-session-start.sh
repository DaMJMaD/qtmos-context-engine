#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${QTMOS_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
PYTHON_BIN="${QTMOS_PYTHON:-python3}"

cd "$ROOT"

"$PYTHON_BIN" -m bridges.alpha.cli observe-host-session \
  --stage gnome-handoff \
  --recovery-hint observe_only
