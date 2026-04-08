# QTMoS Alp-Beta

QTMoS Alp-Beta is a local-first context-integrity and containment engine.

It watches what software surface is active, what web page is actually present, what human-side context is available, what risky execution is being attempted, and what policy action makes sense next. It keeps the raw event line, rebuilds current state from that truth, then projects trust and policy without hiding the reasoning.

## What Makes It Different

- One append-only bus shared across very different observer lanes
- Conservative trust: `trusted`, `shifted`, `suspicious`, `unknown`
- Separate trust and policy layers, so the system can say "this looks aligned" and "still review this package"
- First-class containment through QTF instead of pretending the host is always safe
- Human-loop integration through AHK instead of silent hidden automation

## Current Alpha Lanes

- `surface.observe`: active desktop surface facts
- `web.observe`: active browser/page facts
- `mindseye.vitals`: human/context seam from AHK
- `ahk.feedback`: operator response back into the bus
- `package.install.observe`: risky package intent
- `qtf.execution`: containment execution evidence
- `host.session.observe`: session handoff breadcrumbs

## Architecture Rules

- Raw line first, meaning second
- The bus is truth
- Rebuilt state is current meaning
- Policy is a recommendation layer
- Projection is not allowed to overwrite the source event
- Binding is evidence, not proof

## Repo Layout

```text
QTMoS Alp-Beta/
  bridges/
  config/
  docs/
  hosts/
  runtime/
  schemas/
```

Core architecture docs:

- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [WHITEPAPER_CURRENT.md](docs/WHITEPAPER_CURRENT.md)
- [BUSYDAWG_3D_PLAN.md](docs/BUSYDAWG_3D_PLAN.md)
- [SELF_ARCHITECTURE.md](docs/SELF_ARCHITECTURE.md)
- [INTEGRATIONAL_AWARENESS.md](docs/INTEGRATIONAL_AWARENESS.md)

## Quick Start

Run the local Alpha bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Open the local read-only console:

- `http://127.0.0.1:8765/alpha/console`

Print a human-readable trust summary:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

Rebuild state/tags/projection explicitly:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli cycle
```

Reset the runtime for a fresh local test bed:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli reset-alpha
```

Archive before reset if you want to preserve a snapshot:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli reset-alpha --archive
```

## Validation

Run the regression packs without touching live runtime state:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli validate-browser
python3 -m bridges.alpha.cli validate-mindseye
python3 -m bridges.alpha.cli validate-policy
python3 -m bridges.alpha.cli validate-package
python3 -m bridges.alpha.cli validate-qtf
python3 -m bridges.alpha.cli validate-host-session
python3 -m bridges.alpha.cli validate-messy
```

## Browser Observer

Start the bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Then load the unpacked Chrome/Chromium extension from:

- `bridges/browser-observer/chrome`

Observer docs:

- [bridges/browser-observer/chrome/README.md](bridges/browser-observer/chrome/README.md)
- [schemas/web-observe.example.json](schemas/web-observe.example.json)

## AHK / Mind's Eye Seam

By default QTMoS looks for a shared folder at `~/qtmos-share`.
If your AHK bridge publishes somewhere else, set `QTMOS_SHARE_DIR` explicitly:

```bash
export QTMOS_SHARE_DIR="/path/to/qtmos-share"
```

Ingest the shared context seam:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli ingest-mindseye
```

Publish the latest policy decision into the AHK hook channel:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli publish-ahk-hook
```

Ingest operator feedback back into Alpha:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli ingest-ahk-feedback
```

Seam examples:

- [schemas/mindseye-vitals.example.json](schemas/mindseye-vitals.example.json)
- [schemas/ahk-policy-hook.example.json](schemas/ahk-policy-hook.example.json)
- [schemas/ahk-feedback.example.json](schemas/ahk-feedback.example.json)

## Policy, QTF, and Package Routing

Default declarative policy rules live at:

- `config/policy_rules.json`

Run a local command inside the offline QTF cage:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli qtf-run --workspace /path/to/local/project -- /bin/sh -lc 'pwd && ls -1'
```

Observe a package install and route it into QTF:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-package \
  --manager npm \
  --operation install \
  --package-name local-demo \
  --source-kind local \
  --workspace /path/to/local/project \
  --route-qtf \
  -- /bin/sh -lc 'pwd && ls -1'
```

Related schemas:

- [schemas/qtf-execution.example.json](schemas/qtf-execution.example.json)
- [schemas/surface-observe.example.json](schemas/surface-observe.example.json)
- [schemas/bus-event.example.json](schemas/bus-event.example.json)

## Host Session Breadcrumb

Emit a session breadcrumb manually:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-host-session --stage gnome-handoff --recovery-hint observe_only
```

Record an explicitly suspicious handoff:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-host-session \
  --stage gnome-handoff \
  --compromise-suspected \
  --recovery-hint lockdown_ready \
  --suspicion-note "Unexpected session state after login"
```

Autostart templates:

- `hosts/qtmos-alpha-session.desktop`
- `hosts/qtmos-alpha-session-start.sh`

The desktop entry assumes `"$HOME/Desktop/QTMoS Alp-Beta"` by default. If your checkout lives elsewhere, set `QTMOS_ROOT` before enabling the autostart entry.

## Runtime Files

`runtime/` is generated local state. It is intentionally ignored in Git and rebuilt from events during normal use.

The most useful live files while testing are:

- `runtime/bus/events.jsonl`
- `runtime/state/latest-state.json`
- `runtime/state/busydawg-state.json`
- `runtime/tags/latest-tags.json`

## Publish Notes

Before publishing:

- keep generated runtime state out of git
- keep machine-specific paths out of docs and startup scripts
- keep private adapters, heuristics, or local-only data out of the public tree
- use the validation packs as your pre-push smoke test

The project is strongest when presented as:

`local operational-context engine + conservative trust + explicit policy + containment by cage`
