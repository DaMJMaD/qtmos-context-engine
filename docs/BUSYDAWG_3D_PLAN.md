# BusyDawg 3D Plan

## Why BusyDawg Matters

BusyDawg is not just a visual demo set.
It is one of the clearest surviving expressions of QTMoS state logic in spatial form.

Across the older trees, BusyDawg repeatedly appears as:

- a rail pulse viewer
- a hierarchical point topology
- a hot-point traversal system
- a shell and frame logic surface
- a bridge between state and visible motion

## What The Old Files Suggest

From the legacy files:

- BD-1 defines a base 3D rail pulse with 108 points arranged across six face rings
- larger BusyDawg variants are built by nesting or tiling the lower-order topology
- a hot point advances through the space while the surrounding cloud persists as the current field
- wire boxes and shells show rail boundaries and grouping extents
- QTMoS cortex viewers use voxel and trail state in a similar projector role

This implies a design rule:

BusyDawg is a spatial state topology that can consume projected state from the bridge.

## Working Role In Alp-Beta

BusyDawg belongs between the state layer and the host layer.

It should function as:

- a deterministic spatial projection target
- a 3D representation of current rail and tag conditions
- a host-agnostic output that browser, AHK, OpenGL, or VisPy viewers can render

## Alpha Goal

Alpha does not need to reimplement all BD variants.

Alpha only needs to prove that a state rebuild can emit a valid BusyDawg projection payload.

Start with:

- BD-1 compatible projection
- one active hot point
- one cloud of active nodes
- one rail color set
- one shell/frame set

Suggested Alpha output:

- `runtime/state/busydawg-state.json`

## Suggested Projection Contract

The projection file should contain:

- topology id
- point count
- active indices
- hot index
- rail colors
- shell extents
- pulse frame
- source event ids or source state timestamp

## Alpha Projection Rules

Example rules:

- `memory.note` may mark a subject node group active
- `state.set` may change the current rail color or shell emphasis
- `host.handoff` may move the hot point or target band
- stale or conflict tags may shift a node group toward `-rail`
- valid current state may shift a node group toward `+rail`

## Beta Expansion

Once Alpha is stable, Beta can support:

- multiple BusyDawg topologies
- topology registry
- projector plugins
- live stream updates
- browser and native viewers
- telemetry-driven spatial projection

## Design Rule

Do not let BusyDawg become a second source of truth.

The bus is truth.
State is rebuildable meaning.
BusyDawg is spatial projection.
