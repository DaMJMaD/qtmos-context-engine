# QTMoS Implementation Plan

## Objective

Turn QTMoS into a buildable engine with a clear bridge path:

- Alpha proves the raw bus, shared state, and host handoff
- Beta matures the bridge into a proper local service

## Phase 0: Ground Rules

Status: now

- One runtime truth
- One bus truth
- Zero shadow runtimes
- Hosts are replaceable
- Raw line first, interpretation second

## Phase 1: Alpha Bridge

Goal: prove the loop with the fewest moving parts

Deliverables:

- `runtime/bus/events.jsonl`
- `runtime/state/latest-state.json`
- `runtime/tags/latest-tags.json`
- `runtime/state/busydawg-state.json`
- one event envelope schema
- one replay tool
- one state rebuild tool
- one host adapter

Alpha event types:

- `host.capture`
- `host.selection`
- `bridge.handoff`
- `model.request`
- `model.response`
- `memory.note`
- `state.snapshot`
- `operator.tag`
- `busydawg.project`

Alpha rules:

- append only
- local only
- JSONL only
- no daemon required
- at least one host writes and one host reads

Definition of done:

- Host A writes an event
- QTMoS rebuilds state
- Host B reads the same context
- tags and rails exist without mutating the source event
- BusyDawg projection can be rebuilt from the same event line

## Phase 2: Beta Bridge

Goal: convert the proven pattern into a reusable service

Deliverables:

- local bridge daemon
- HTTP API
- optional MCP adapter
- websocket or stream output
- typed decode modules
- state projector registry
- tag and rail projector registry
- host adapter contracts
- BusyDawg topology and projection registry

Beta event families:

- text and prompt events
- tool and command events
- memory and policy events
- telemetry and machine events
- optional CAN/J1939 frame ingest

Definition of done:

- multiple hosts can attach cleanly
- state can be replayed from raw log
- decoders can be added without changing the bus format
- unknown payloads survive intact

## Recommended Build Order

1. Define event schema
2. Define state snapshot schema
3. Build JSONL appender
4. Build replay reader
5. Build state projector
6. Build BusyDawg projector
7. Build rail and tag projector
8. Wire first host
9. Add second host
10. Promote to daemonized Beta

## First Three Concrete Tasks

### Task 1: Bus Envelope

Write the event schema and freeze its first version.

### Task 2: State Rebuilder

Build the logic that scans the event log and materializes latest state.

### Task 3: First Host Adapter

Use either a local shell host or terminal as the first host.
The first host must emit `host.capture` and read `bridge.handoff`.

### Task 4: BusyDawg Projection

Project rebuilt state into a simple BusyDawg output file.
Start with BD-1 compatible projection rules before scaling upward.

## Stretch Direction

After Beta is stable:

- add AHK HUD overlay host
- add web host
- add read-only SocketCAN/J1939 ingest
- add BusyDawg live projector host
- add decoded telemetry overlays
- add context pack export and import
