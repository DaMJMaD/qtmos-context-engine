# Alpha Bridge

## Purpose

Alpha is the smallest serious bridge that proves QTMoS can share working context across hosts without inventing a heavy service too early.

## Alpha Structure

```text
bridges/alpha/
  README.md
  __init__.py
  appender.py
  cli.py
  ext.py
  models.py
  paths.py
  project_busydawg.py
  project_tags.py
  rebuild_state.py

runtime/
  bus/
    events.jsonl
  state/
    latest-state.json
    busydawg-state.json
  tags/
    latest-tags.json
```

## Alpha Responsibilities

- accept local host events
- append every event to `events.jsonl`
- preserve raw payloads
- project current state into `latest-state.json`
- project rail and tag overlays into `latest-tags.json`

## Alpha Constraints

- local filesystem only
- JSONL append-only bus
- no rewrite of source events
- no network daemon required
- one or two hosts only

## Alpha Event Flow

1. host emits event
2. event appended to bus
3. state projector rebuilds latest state
4. tag and rail projector annotate the event
5. another host reads the rebuilt state or handoff event

## Alpha Success Test

If a Codex capture can be written, tagged, materialized into state, and reopened by a second host, Alpha has done its job.

## Working Commands

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli --help
python3 -m bridges.alpha.cli emit-surface --surface-id x11:0x3e00004 --process-name codex --window-class "codex | Codex" --window-title "Codex" --focused --trust-status trusted
python3 -m bridges.alpha.cli observe-privilege --method sudo --result prompted --target-user root -- /usr/bin/apt install curl
python3 -m bridges.alpha.cli observe-ext --qtf-label pkg-npm-install-local-demo --package-name local-demo --package-manager npm --reason "Requesting promotion after clean QTF"
python3 -m bridges.alpha.cli cycle
python3 -m bridges.alpha.cli ingest-ahk
python3 -m bridges.alpha.cli ingest-mindseye
```

The first real outputs live at:

- `runtime/bus/events.jsonl`
- `runtime/state/latest-state.json`
- `runtime/tags/latest-tags.json`
- `runtime/state/busydawg-state.json`
