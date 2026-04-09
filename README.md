# QTMoS Alp-Beta

QTMoS is a local-first context-integrity and containment engine.

It is built around a simple security idea: a lot of risky moments do not start with a known malware signature. They start when the machine, the browser, the session, the package action, and the human context stop lining up cleanly.

QTMoS watches those seams, keeps the raw event line append-only, rebuilds current state from that truth, and projects trust and policy without hiding the reasoning.

## Why This Exists

Most security tools ask:

- is this known bad
- can we block this hard
- does this match a signature

QTMoS asks a different question:

- does what is happening right now make sense in context

That means it is closer to context integrity, trust drift detection, and containment at risky boundaries than to classic antivirus or heavy-handed host lockdown.

## What QTMoS Does

Today, Alpha can correlate:

- active desktop surface facts
- active browser/page facts
- optional human/context signals from AHK
- privilege-boundary observations such as `sudo`, `su`, `pkexec`, or `doas`
- package-install intent
- offline QTF containment runs
- host-session breadcrumbs after login or handoff

From that, it can project trust such as `trusted`, `shifted`, `suspicious`, or `unknown`, and separately decide policy such as `allow`, `review`, `quarantine`, or `deny`.

## Why The Split Matters

QTMoS intentionally keeps trust and policy separate.

That lets the system say something like:

```text
Overall trust: trusted
Policy: review (package_registry_review)
```

That is not a contradiction. It means the current browser and surface are aligned, while the current package action still deserves caution.

## What Makes It Different

- One append-only bus shared across very different observer lanes
- Conservative trust: binding is evidence, not proof
- Raw event truth stays separate from rebuilt current state and policy
- Containment is first-class through QTF instead of pretending the host is always safe
- Human-loop feedback is explicit instead of hidden behind opaque automation

## What QTMoS Is Not

- not antivirus
- not EDR
- not a rootkit killer
- not trying to own or heavily lock down the entire machine

The current Alpha is strongest at context mismatch, trust drift, containment routing, and making risky actions legible. It is weaker against already-established kernel or firmware compromise, and it is better to say that plainly than to overclaim.

## Try It In Two Minutes

If you just want to see whether the engine is coherent, run the validation packs first:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli validate-browser
python3 -m bridges.alpha.cli validate-policy
python3 -m bridges.alpha.cli validate-package
python3 -m bridges.alpha.cli validate-privilege
python3 -m bridges.alpha.cli validate-qtf
python3 -m bridges.alpha.cli validate-host-session
python3 -m bridges.alpha.cli validate-messy
```

That gives you a zero-drama way to see the trust and policy model work before wiring every live observer lane.

## See The Live Console

Run the local Alpha bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Then open:

- `http://127.0.0.1:8765/alpha/console`

Print a human-readable trust summary:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

Rebuild state, tags, and projection explicitly:

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

## Three Alpha Demo Stories

These are the clearest ways to understand the current project shape:

1. Browser and surface trust drift
QTMoS compares the active browser page and the focused desktop surface, then treats a clean bind very differently from a misleading or sensitive mismatch.

2. Registry package install routed into containment
QTMoS can observe a package action, run it inside QTF, preserve the execution evidence, and still keep policy at `review` if the source is risky enough to warrant it.

3. Suspicious session breadcrumb after login or handoff
QTMoS can preserve a host-session note like `lockdown_ready` or `compromise_suspected` without silently rewriting the story later.

There is a fuller walkthrough in [docs/TEST_DRIVE.md](docs/TEST_DRIVE.md).

## Current Alpha Lanes

- `surface.observe`: active desktop surface facts
- `web.observe`: active browser/page facts
- `mindseye.vitals`: optional human/context seam from AHK
- `ahk.feedback`: operator response back into the bus
- `privilege.observe`: privilege boundary breadcrumbs
- `package.install.observe`: risky package intent
- `qtf.execution`: containment execution evidence
- `host.session.observe`: session handoff breadcrumbs

## Architecture Rules

- raw line first, meaning second
- the bus is truth
- rebuilt state is current meaning
- policy is a recommendation layer
- projection is not allowed to overwrite the source event
- binding is evidence, not proof

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

Core docs:

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/WHITEPAPER_CURRENT.md](docs/WHITEPAPER_CURRENT.md)
- [docs/BUSYDAWG_3D_PLAN.md](docs/BUSYDAWG_3D_PLAN.md)
- [docs/SELF_ARCHITECTURE.md](docs/SELF_ARCHITECTURE.md)
- [docs/INTEGRATIONAL_AWARENESS.md](docs/INTEGRATIONAL_AWARENESS.md)

## Browser Observer

Start the bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Then load the unpacked Chrome or Chromium extension from:

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

## Feedback And Contributions

If you try QTMoS and it confuses you, breaks, or feels promising in a way the README did not explain well, that is useful feedback.

The fastest way to help right now is:

- try one validation pack and tell me where the wording feels unclear
- try the local console and tell me what feels obvious versus mysterious
- open an issue with sanitized output, screenshots, or a short write-up of what you expected

Contributor notes live in [CONTRIBUTING.md](CONTRIBUTING.md).
