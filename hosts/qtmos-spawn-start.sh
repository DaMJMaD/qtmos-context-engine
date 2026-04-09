#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
URL="${QTMOS_SPAWN_URL:-http://127.0.0.1:8765/alpha/spawn}"
LOG_DIR="$ROOT/runtime/logs"
LOG_FILE="$LOG_DIR/spawn-http.log"

mkdir -p "$LOG_DIR"

ensure_bridge() {
  if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | grep -q ':8765 '; then
    return
  fi

  nohup python3 -m bridges.alpha.cli serve-http >"$LOG_FILE" 2>&1 &
  sleep 1
}

pick_browser() {
  for browser in google-chrome chromium chromium-browser; do
    if command -v "$browser" >/dev/null 2>&1; then
      printf '%s\n' "$browser"
      return 0
    fi
  done
  return 1
}

ensure_bridge

if browser="$(pick_browser)"; then
  exec "$browser" \
    --new-window \
    --app="$URL" \
    --start-maximized
fi

exec xdg-open "$URL"
