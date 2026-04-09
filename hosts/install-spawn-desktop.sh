#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP_FILE="$APPS_DIR/qtmos-spawn.desktop"
ICON_PATH="$ROOT/hosts/trust-console/assets/spawn-sigil.png"
START_SCRIPT="$ROOT/hosts/qtmos-spawn-start.sh"

mkdir -p "$APPS_DIR"

cat >"$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=QTMoS Spawn
Comment=Linux Spawn duality shell for QTMoS
Exec=$START_SCRIPT
Icon=$ICON_PATH
Terminal=false
Categories=Development;Security;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE"
echo "Installed desktop entry:"
echo "$DESKTOP_FILE"
