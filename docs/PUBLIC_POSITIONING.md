# QTMoS Public Positioning

This file is the plain-English copy pack for talking about QTMoS in public without drifting into hype, mystical wording, or overclaiming.

## Core Thesis

QTMoS is a local-first context-integrity engine that reconstructs trust from immutable runtime history, contains risky actions in QTF, and requires explicit promotion through EXT.

## Repo Description

Use this as the short GitHub description:

`Local-first context-integrity engine. Reconstructs trust from immutable runtime history, contains risky actions in QTF, and gates promotion through EXT.`

## One-Paragraph Pitch

QTMoS is a local-first context-integrity and containment engine. It watches the seams between desktop surface, browser reality, host session, package intent, privilege boundaries, and optional human context, then rebuilds current trust from an append-only event history instead of blindly trusting the live snapshot. Risky actions can run inside QTF, and nothing leaves that containment path cleanly without an explicit EXT promotion step.

## What QTMoS Is

- a local-first context-integrity engine
- a trust-and-policy layer for risky software boundaries
- an append-only event-sourced runtime model
- a containment and promotion model built around QTF and EXT

## What QTMoS Is Not

- not antivirus
- not EDR
- not a rootkit killer
- not heavy-handed machine lockdown
- not a claim to solve every layer of compromise

## Why It Feels Different

- It asks `does this make sense in context` instead of only `is this known bad`.
- It treats current state as something rebuilt from history, not something automatically trusted.
- It keeps trust and policy separate, so the system can be honest without becoming unreadable.
- It makes containment success and promotion permission two different things.

## Three Short Lines

Use these when someone wants the quick version:

- `QTMoS watches where system stories stop matching.`
- `It rebuilds trust from immutable runtime history.`
- `It contains first, then requires explicit promotion.`

## Pinned Profile Blurb

Use this for a GitHub profile README or short bio section:

`Building QTMoS: a local-first context-integrity engine for reconstructing trust from runtime history, containing risky actions in QTF, and gating promotion through EXT.`

## Launch Post

Use this when you want a public post that sounds human and not try-hard:

```text
I’ve been building QTMoS, a local-first context-integrity and containment engine.

The idea is simple: a lot of risky moments don’t start with a malware signature. They start when the browser, desktop, host session, package action, or human context stop lining up cleanly.

QTMoS keeps an append-only runtime history, rebuilds current trust from that history, contains risky actions in QTF, and now requires explicit promotion through EXT instead of silently assuming containment success is enough.

Still alpha, but the shape is real:
- browser and desktop trust drift
- package actions routed into containment
- privilege and host-session breadcrumbs
- trust kept separate from policy

Repo: https://github.com/DaMJMaD/qtmos-context-engine
```

## Shorter Post

```text
QTMoS is a local-first context-integrity engine.

It reconstructs trust from immutable runtime history, contains risky actions in QTF, and requires explicit promotion through EXT.

It’s alpha, but it already shows browser/surface drift, package containment, privilege boundaries, and session breadcrumbs in one readable model.

https://github.com/DaMJMaD/qtmos-context-engine
```

## Topics

Good GitHub topics for QTMoS:

- `cybersecurity`
- `security-tooling`
- `browser-security`
- `containment`
- `sandbox`
- `policy-engine`
- `trust`
- `event-sourcing`
- `python`

## Message Discipline

If a feature or post does not make QTMoS better at one of these, it probably weakens the story:

- reconstructing trust
- containing risk
- gating promotion
- explaining why policy fired
