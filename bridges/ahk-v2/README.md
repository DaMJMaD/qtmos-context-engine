# QTMoS AHK v2 Bridge

This bridge gives QTMoS a Linux-first AutoHotkey v2 entrypoint through Wine.

What it does:
- runs AHK v2 on Linux via the local `ahk-v2` wrapper
- loads default QTMoS bridge knowledge
- supports `status`, `defaults`, `learn`, and `record`
- writes append-only JSONL logs for later ingestion into the Alpha bus
- is the home for future `surface.observe` events from AHK and spy tools

What it is not:
- not native Linux window automation
- not a full replacement for the old Windows game-control scripts
- not yet wired directly into `events.jsonl`

Current shape:
- `qtmos_bridge.ahk`: AHK v2 bridge runtime
- `run-linux.sh`: Linux launcher
- `data/default_knowledge.txt`: starter QTMoS defaults
- `data/learn.jsonl`: appended learning notes
- `data/record.jsonl`: appended record events

Usage:

```bash
./bridges/ahk-v2/run-linux.sh status
./bridges/ahk-v2/run-linux.sh defaults
./bridges/ahk-v2/run-linux.sh learn "Preserve the line."
./bridges/ahk-v2/run-linux.sh record host local-shell "manual test"
```

Integration direction:
- AHK v2 stays the personal interaction layer.
- QTMoS stays the truth/state engine.
- This bridge is the handoff seam between them.
- Spy and surface tools should emit observation events into the bus instead of acting as side channels.
