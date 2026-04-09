# QTMoS Claude Guidance

You are operating inside the QTMoS project.

## Mission

Help with QTMoS as a local-first context-integrity and containment engine.

Current public thesis:

- reconstruct trust from immutable runtime history
- contain risky actions in QTF
- require explicit promotion through EXT

## Working Style

- be concise and practical
- prefer reading before editing
- explain what you plan to do in plain language
- keep answers short unless asked for depth
- optimize for real users understanding what changed

## Usage Discipline

- avoid long speculative essays
- keep tool use lean
- prefer low-churn edits
- prefer one-shot print mode for bounded checks
- use interactive mode only for multi-step work
- do not install packages or reach for network access unless explicitly asked
- do not start long-running background processes unless explicitly asked

## Codebase Rules

- preserve the trust-versus-policy split
- preserve the append-only bus as truth
- treat rebuilt state and projections as derived views, not source truth
- avoid mystical wording when editing public docs
- prefer deterministic demo and validation paths over clever hidden behavior

## Safety

- never run destructive git commands
- do not overwrite user changes
- do not delete runtime or config data unless asked
- sanitize personal paths, hostnames, boot IDs, and tokens before suggesting public output

## Terminal Collaboration

When working under a supervisor, keep responses in this shape when helpful:

1. `Read:` what you inspected
2. `Plan:` what you think should happen next
3. `Result:` what you changed or learned

Default to short responses that fit comfortably in a terminal pane.
