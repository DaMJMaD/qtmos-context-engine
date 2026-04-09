#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GUIDANCE="$(cat "$ROOT/CLAUDE.md")"
SESSION_FILE="$ROOT/.git/claude-bottom-session-id"
MODEL="${CLAUDE_MODEL_OVERRIDE:-qwen3.5}"

export CLAUDE_CODE_NO_FLICKER=1

new_session_id() {
  python3 - <<'PY'
import uuid
print(uuid.uuid4())
PY
}

ensure_session() {
  if [[ ! -f "$SESSION_FILE" ]] || [[ ! -s "$SESSION_FILE" ]]; then
    mkdir -p "$(dirname "$SESSION_FILE")"
    new_session_id > "$SESSION_FILE"
  fi
  cat "$SESSION_FILE"
}

run_prompt() {
  local prompt="$1"
  local session_id
  session_id="$(ensure_session)"

  claude \
    --bare \
    --add-dir "$ROOT" \
    --append-system-prompt "$GUIDANCE" \
    --model "$MODEL" \
    --effort low \
    --permission-mode default \
    --max-budget-usd 0.25 \
    --session-id "$session_id" \
    -p \
    "$prompt"
}

if [[ "${1:-}" == "--reset" ]]; then
  rm -f "$SESSION_FILE"
  echo "Claude bottom session reset."
  exit 0
fi

if [[ $# -gt 0 ]]; then
  run_prompt "$*"
  exit 0
fi

cat <<'EOF'
QTMoS Claude Bottom Chat

- Type a prompt and press Enter.
- Commands: /usage, /reset, /exit
- Model: ${MODEL}
- This mode keeps a lightweight Claude session without the full-screen TUI.
EOF

while true; do
  printf '\n%s' 'you> '
  IFS= read -r prompt || break

  case "$prompt" in
    "")
      continue
      ;;
    /exit)
      break
      ;;
    /reset)
      rm -f "$SESSION_FILE"
      echo "Claude bottom session reset."
      continue
      ;;
    /usage)
      "$ROOT/scripts/claude-usage.py"
      continue
      ;;
  esac

  printf '\n%s\n' 'claude>'
  run_prompt "$prompt"
done
