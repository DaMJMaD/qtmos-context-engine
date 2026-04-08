# QTMoS Whitepaper

Current as of April 8, 2026

## Abstract

QTMoS is a local-first operational-context engine.

Its purpose is to preserve raw truth about what the machine is doing, rebuild the latest known state from that truth, score trust conservatively across multiple observers, and project that judgment into clear operator-facing actions without hiding the reasoning.

In plain language:

QTMoS watches what software surface is active, what web page is actually present, what human-side context is available, what risky execution is being attempted, and what policy action makes sense next. It records those facts on one append-only line, rebuilds them into a shared state, and exposes them through reports, BusyDawg projection, AHK reactions, and validation scenarios.

This whitepaper describes the current Alpha system as it actually exists today.

## The Core Idea

QTMoS is built around one very simple rule:

**raw line first, meaning second**

That leads to a clean structure:

- the bus is truth
- rebuilt state is current meaning
- policy is a recommendation layer
- BusyDawg is a projection layer
- hosts are replaceable views and emitters

This is important because most systems collapse observation, interpretation, and action into one blurry step. QTMoS keeps them separated on purpose.

## What Is Original Here

QTMoS is not original because it has a log, a dashboard, or a sandbox. Lots of systems have those.

What feels genuinely original in QTMoS is the combination:

### 1. One append-only truth line shared across very different observers

Desktop surface events, browser observations, AHK-side human context, QTF containment runs, package-intent events, host-session breadcrumbs, and operator feedback all land on the same event bus and are rebuilt into one state.

That is not a normal browser security tool, not a normal EDR, not a normal assistant runtime, and not a normal AHK automation stack.

### 2. Trust is treated as conservative context, not magic classification

QTMoS does not try to claim it "knows" everything. Its current trust model is deliberately narrow:

- `trusted`
- `shifted`
- `suspicious`
- `unknown`

And one design rule matters a lot:

**binding is evidence, not proof**

That single rule prevents many over-trust failures.

### 3. Host identity is separated from page subject

QTMoS learned this through a real false positive. A legitimate GitHub page was being treated too much like the brand words on the page instead of the host it was actually on.

The fix was to separate:

- **host identity** as the primary anchor
- **page subject/content** as secondary context

That is now one of the clearest design lessons in the project.

### 4. Human-side context is part of the same truth system

The legacy AHK context lane is not just an overlay or toy input. It is a structured observer lane with real ingest, binding, reporting, tags, validation, and BusyDawg projection.

Then AHK feedback closes the loop:

- QTMoS policy goes out to AHK
- AHK prompts or reacts
- user response comes back in as `ahk.feedback`

That creates a real bidirectional human-machine context loop.

### 5. Containment is being built as a first-class lane, not as a side feature

QTF is not just "run a command elsewhere." It is being shaped as the disposable execution cage for risky actions.

QFS is being treated as the evidence locker.

EXT is planned as the promotion gate.

That makes the architecture unusually clean:

**QTF runs -> QFS records -> EXT promotes or denies**

### 6. Passive choke points instead of secret takeover logic

QTMoS does not need to pretend it owns BIOS, GRUB, or hidden recovery trapdoors from user space.

Instead, it is being built around calm, explicit, auditable choke points:

- GNOME/session handoff
- privilege boundaries
- risky install routing
- QTF promotion boundaries

That is a much more honest and durable security posture.

## System Architecture

The current Alpha shape is:

```text
observers -> append-only bus -> rebuild state -> trust/policy -> projection -> operator reaction
```

Today that means:

- observer lanes emit events
- events are appended to the JSONL bus
- state is rebuilt from the log
- trust and policy are derived after observation
- BusyDawg and tags project the result
- AHK and reports react to the projection

## Current Observer Lanes

### 1. `surface.observe`

This lane tracks the active software surface on Linux X11.

It records facts like:

- active window title
- process name and path
- window class
- bounds
- focus state
- stable surface identity

This is the foundation for knowing where QTMoS is actually standing.

### 2. `web.observe`

This lane comes from the browser observer.

It records facts like:

- URL
- origin
- domain
- title
- text snippet
- mutation signal
- tab and window identity

It binds browser context to the active desktop surface and is the basis of current browser trust scoring.

### 3. `mindseye.vitals`

This is the legacy lane name for the AHK context seam.

It records things like:

- condition
- stage
- focus level
- stress level
- intent signal
- raw context text when present

It is now Linux-normalized, bound to active surface and web context, and visible in report, tags, and BusyDawg as generic human/context input rather than D2R-specific telemetry.

### 4. `ahk.feedback`

This lane records human response coming back from AHK review prompts.

It currently captures responses like:

- `continue`
- `decline`
- `timeout`

This is one of the strongest proofs that QTMoS is not only observing. It is participating in a human loop without collapsing into hidden automation.

### 5. `package.install.observe`

This lane records explicit package-install intent as first-class context.

It currently supports package-aware context such as:

- package manager
- operation
- source kind
- lockfile state
- scripts policy
- whether QTF routing was requested

This is not a fake background sniffer. It is explicit and auditable.

### 6. `qtf.execution`

This lane records execution inside the containment cage.

It captures:

- backend used
- command run
- workspace context
- stdout/stderr
- exit code
- duration
- file changes

On this machine, QTF currently uses `podman` as the honest backend because `bubblewrap` is installed but not usable from this session.

### 7. `host.session.observe`

This lane starts a breadcrumb at GNOME/session handoff.

It records:

- hostname
- desktop/session type
- boot id
- session stage
- suspicion state
- recovery hint
- suspicion note

This is the first host-side breadcrumb for "the session felt wrong."

## Trust Model

The current trust states are:

- `trusted`
- `shifted`
- `suspicious`
- `unknown`

These are not meant to be philosophical labels. They are operational.

Very roughly:

- `trusted` means the active signals align strongly enough to work from
- `shifted` means identity or context drift occurred
- `suspicious` means there is meaningful risk or contradiction
- `unknown` means evidence is too weak to decide

QTMoS does not try to solve global truth. It tries to preserve enough structured caution to be useful.

## Policy Model

QTMoS now has a small declarative policy layer with these actions:

- `allow`
- `warn`
- `review`
- `quarantine`
- `deny`

This layer is intentionally downstream from trust. It does not rewrite trust. It reacts to it.

That policy layer is now aware of:

- browser/surface trust
- human context
- package source kind
- lockfile state
- scripts policy
- QTF success or failure

This has already created useful behavior:

- suspicious sensitive pages can map to `deny`
- unknown weak observations map to `review`
- registry-sourced package flows stay in `review`
- failed QTF package runs map to `quarantine`
- clean local package flows with successful QTF can map to `allow`

## BusyDawg and Projection

BusyDawg remains projection-only.

That separation is one of the strongest parts of the architecture:

- bus = truth
- state = materialized meaning
- BusyDawg = spatial/operator projection

This keeps the system auditable and avoids circular reasoning.

BusyDawg currently projects nodes and edges across:

- active surface
- active web page
- active binding
- active human context
- active policy
- active package flow
- active QTF run
- active host session
- active AHK feedback

## AHK Integration

QTMoS now has a real bidirectional AHK seam.

### Outbound

QTMoS policy auto-publishes structured AHK hook events.

AHK can react differently by action:

- `allow`
- `warn`
- `review`
- `quarantine`
- `deny`

### Inbound

AHK can write operator response back into the system as `ahk.feedback`.

This makes the operator part of the loop instead of just a viewer.

## QTF, QFS, and EXT

This is the cleanest high-level split in the project right now:

### QTF

QTF is the disposable execution cage.

Its job is to let risky work happen where it cannot directly touch the real host in normal ways.

### QFS

QFS is the evidence locker.

Its future role is to hold capture bundles, manifests, hashes, and replayable evidence.

The current QTF capture data is already pointing in that direction, even if the full QFS format is not the active implementation focus yet.

### EXT

EXT is the promotion gate.

It is not fully built yet in Alpha.

Its intended role is:

- nothing leaves QTF silently
- promotion is explicit
- promotion is policy-gated
- promotion is logged

That is the right next shape for host-safe execution.

## What Works Today

As of today, QTMoS can already do all of this in one coherent Alpha:

- observe the active Linux surface
- observe the active browser page
- bind browser to surface
- score trust conservatively
- explain why it chose that trust state
- ingest AHK human context
- bind that context to the active surface and web page
- derive a declarative policy action
- auto-publish that policy to AHK
- capture AHK operator feedback back into state
- route explicit package-install observations into QTF
- score package risk using source kind, scripts, lockfile state, and QTF outcome
- record host-session breadcrumbs at GNOME handoff
- project all of this into BusyDawg and human-readable reports

That is already much more than a demo.

## Validation Status

Current validation status is fully green:

- Browser trust: `5/5 passed`
- AHK context correlation: `1/1 passed`
- Policy: `5/5 passed`
- Full-chain messy pack: `4/4 passed`
- AHK feedback: `1/1 passed`
- QTF: `1/1 passed`
- Package: `5/5 passed`
- Host session: `1/1 passed`

The project is not just "seems to work." It has a growing regression harness.

## Live Current Snapshot

At the time of this whitepaper, the live report shows:

- overall trust: `trusted`
- policy: `review (package_registry_review)`
- surface: Example Domain in Chrome
- web trust: `trusted`
- AHK context: stable and high-bound to the active browser surface
- host session: GNOME handoff breadcrumb marked suspected with `lockdown_ready`
- package flow: registry-sourced package routed through QTF
- QTF backend: `podman`

This is a good example of how multiple lanes can coexist:

- browser trust can be calm
- while package policy remains cautious
- while host-session breadcrumbing remains suspicious

QTMoS is not flattening that into one fake simple answer. It keeps the layers visible.

## What QTMoS Is Not

QTMoS is not:

- a finished security product
- a hidden rootkit
- a BIOS or bootloader replacement
- a fully automatic malware prevention platform
- a generic chatbot with a fancy log

It is a local operational-context engine with a growing set of security-relevant lanes.

## Why This Matters

Most compromises do not happen because the machine lacked one more alert.
They happen because the system did not preserve enough context to make safe decisions at the right forks.

QTMoS is trying to create those forks.

Not through invisibility.
Not through fake omniscience.
Through:

- better observation
- clearer rebuildable context
- conservative trust
- controlled containment
- explicit promotion
- visible operator feedback

That is a strong long-term direction.

## Where The Architecture Feels Strongest

The strongest parts of the system right now are:

- the strict separation between bus, state, policy, and projection
- the conservative trust model
- the human-machine loop through AHK
- the host-vs-subject modeling fix
- the honest containment direction with QTF
- the use of passive choke points instead of hidden takeover logic

## Where The Architecture Is Still Young

The most obvious unfinished areas are:

- EXT promotion gate is not fully implemented yet
- QFS as a formal sealed evidence format is not the dominant active workflow yet
- privilege/sudo breadcrumbing is not built yet
- early-boot coverage does not exist below user-space session handoff
- package routing is explicit, not yet ambient
- QTF still needs deeper capture if it is going to support heavier threat analysis later

These are not failures. They are the clean frontiers.

## The Three Best Next Directions

### 1. Passive privilege boundary lane

Build a `privilege.observe` lane for the sudo/auth boundary.

This matches the current choke-point philosophy perfectly.

### 2. EXT promotion gate

Finish the rule that nothing leaves QTF without an explicit, logged, policy-gated promotion step.

This would complete the current containment arc.

### 3. Recovery lane from host-session suspicion

Turn `recovery_hint` into a concrete but auditable response path, such as:

- lock down promotion
- elevate review friction
- pause risky package routing
- increase operator prompts

This would make host-session breadcrumbs more than passive memory.

## Short Human Verdict

QTMoS is now a real, unusual, and coherent Alpha system.

Its originality is not in any one file or one trick.
Its originality is in the architecture:

- one truth bus
- many observer lanes
- conservative trust
- explicit policy
- human feedback
- containment by cage
- promotion by gate
- projection without lying about certainty

That is enough to say this is no longer just a concept.

It is a working local operational-context engine with real security potential.
