#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v ahk-v2 >/dev/null 2>&1; then
  echo "[QTMoS AHK]: ahk-v2 launcher not found in PATH." >&2
  exit 1
fi

exec ahk-v2 "$SCRIPT_DIR/qtmos_bridge.ahk" "$@"
