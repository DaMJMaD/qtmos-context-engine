# QTMoS Architecture

## Working Definition

QTMoS is a local-first context-integrity engine.

It treats the append-only event line as truth, rebuilds current state from that history, and projects trust, policy, and operator-facing views without overwriting the raw record.

The bridge is the shared layer that lets raw events, interpretation, state, and hosts stay connected without turning every integration into a new runtime.

Short operational model:

- observe the seams
- append raw truth
- rebuild current meaning
- separate trust from policy
- contain in QTF
- require explicit promotion through EXT

## Source Lessons Integrated Here

This architecture is built from the patterns that kept repeating across:

- old AHK pulse and HUD systems
- BusyDawg hierarchical 3D state viewers
- leader/follower sync logic
- QTMoS rail and quad interpretation
- Tenchin supervisor patterns
- local-first routing and model switching
- CAN/J1939 style thinking about a shared line with layered interpretation

## The Five Layers

### 1. Bus Layer

The bus layer is the authoritative line.

Rules:

- append-only
- timestamped
- immutable after write
- no summary may replace the original event
- every downstream view points back to the original event id

Examples:

- host capture event
- surface observe event
- focus change event
- model request
- model response
- memory write
- decoded vehicle frame
- operator annotation

### 2. Decode Layer

The decode layer turns raw events into structured meaning when possible.

Rules:

- preserve unknown events cleanly
- decode where schemas or rules exist
- mark uncertain decodes instead of pretending certainty
- do not drop raw payloads

Examples:

- text selection -> host capture object
- X11 or HWND sample -> surface observation object
- JSONL payload -> typed command event
- J1939 frame -> PGN/SPN decode

### 3. State Layer

The state layer builds the latest known picture from the event line.

Rules:

- state is materialized from events
- state can be rebuilt from the log
- state snapshots are caches, not truth
- stale detection is mandatory

Examples:

- latest selected text per host
- current conversation handoff
- last known health metric
- current active model
- current decoded machine state

The state layer must also be able to materialize a BusyDawg-ready projection payload.

### 3.5. BusyDawg Projection Layer

BusyDawg is the spatial state logic surface for QTMoS.

It should be treated as a projection layer that turns event and state changes into:

- active nodes
- hot points
- shell or block activations
- color or rail state
- pulse timing
- spatial grouping

This keeps BusyDawg aligned with the bridge:

- bus remains truth
- state remains deterministic
- BusyDawg becomes a spatial projection of the current state

BusyDawg is not the authoritative source of truth.
BusyDawg is the authoritative visual-spatial projection of that truth.

### 4. Tag Layer

The tag layer adds commentary and overlays.

Tags never replace the source event.

Core tags:

- changed
- stale
- invalid
- derived
- unverified
- proprietary
- operator_marked
- conflict

### 5. Host Layer

Hosts are replaceable views and emitters.

Examples:

- operator pane
- terminal shell
- AHK HUD overlay
- AHK spy bridge
- Linux Window Spy
- web dashboard
- future CAN monitor

Hosts do not own truth.
Hosts publish to and read from the bridge.

### Surface Observer Rule

Surface observers are allowed to report what software surface QTMoS is actually standing on.

Examples:

- active window change
- process and class identity
- bounds and focus state
- visible text snapshots
- stable surface signatures

Surface observers do not decide trust on their own.
They publish observations.
QTMoS state, rails, BusyDawg, and policy decide what those observations mean.

## Rail Interpretation Model

Each event may be projected into rails:

- `0rail`: raw canonical line
- `-rail`: inverse, failure, risk, tension, stale, caution
- `+rail`: valid meaning, useful intent, healthy state, proposed action
- `pm_rail`: fused output that keeps the conflict visible

The rail model is a structured interpretation grammar.
It is not allowed to overwrite the source event.

## Alpha Bridge

Alpha is intentionally simple.

It exists to prove the architecture fast.

Components:

- append-only JSONL event log
- one runtime state snapshot
- one tag overlay file
- one BusyDawg projection snapshot
- one or two hosts only
- local filesystem coordination

Alpha is successful when two different hosts can share one working context through the same raw bus and rebuilt state.
Alpha is stronger when that same rebuilt state can also drive one BusyDawg projection file.

## Beta Bridge

Beta turns the bridge into a proper service.

Components:

- bridge daemon
- typed event API
- append-only event store
- decode modules
- state projectors
- tag and rail engine
- host adapters
- BusyDawg projector modules
- optional read-only CAN/J1939 ingest

Beta is successful when multiple hosts, services, and decoders can share one event truth without forking behavior.

## Safety Rules

- first real CAN/J1939 support is read-only
- raw data is never destroyed by interpretation
- actions are logged
- unknown data is preserved, not guessed away
- operator intent stays visible

## Canonical Build Path

1. Alpha JSONL bus
2. One host adapter
3. State projector
4. Rail and tag overlay
5. Replay and rebuild tools
6. Beta daemon and typed APIs
