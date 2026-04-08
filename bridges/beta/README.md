# Beta Bridge

## Purpose

Beta is the mature bridge service built after Alpha proves the model.

## Beta Structure

```text
bridges/beta/
  README.md

service/
  api/
  decode/
  state/
  tags/
  hosts/
  ingest/
```

## Beta Responsibilities

- expose a local service boundary
- accept typed events over HTTP and optional MCP
- keep an append-only event store
- run decoders and state projectors
- publish current state to multiple hosts
- preserve unknown payloads

## Beta Modules

- `api`: host-facing service boundary
- `decode`: event and telemetry parsing
- `state`: materialized latest-known views
- `tags`: overlay, rails, and confidence markers
- `hosts`: Codex, terminal, HUD, web adapters
- `ingest`: optional telemetry sources like read-only CAN/J1939

## Beta Rules

- event truth remains append-only
- state remains rebuildable from the log
- rails remain overlays
- actions are logged
- first machine-bus support is read-only

## Beta Promotion Test

Beta is justified only after Alpha shows:

- stable event envelope
- stable state rebuild
- stable cross-host handoff
- no need to keep inventing one-off host logic
