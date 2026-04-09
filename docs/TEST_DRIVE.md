# QTMoS Test Drive

This is the quickest way to get a feel for QTMoS without wiring every observer lane on day one.

## Path 1: One-Command Showcase

Run the built-in showcase story:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli demo-alpha
```

What this shows:

- phase one: a clean local package runs inside QTF and still stays in `review`
- phase two: an explicit EXT request is recorded and policy moves to `allow`
- containment success and promotion permission are shown as separate decisions

Other showcase stories:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli demo-alpha --story registry-review
python3 -m bridges.alpha.cli demo-alpha --story lockdown-deny
```

Those give you two more sharp stories:

- a registry package still stays in `review` even after EXT is requested
- a suspicious `lockdown_ready` host session can deny promotion at the EXT boundary

## Path 2: Zero-Setup Trust And Policy Sanity Check

Run the built-in validation packs:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli validate-browser
python3 -m bridges.alpha.cli validate-policy
python3 -m bridges.alpha.cli validate-package
python3 -m bridges.alpha.cli validate-ext
python3 -m bridges.alpha.cli validate-privilege
python3 -m bridges.alpha.cli validate-qtf
python3 -m bridges.alpha.cli validate-host-session
python3 -m bridges.alpha.cli validate-messy
```

What this proves:

- the trust model is internally coherent
- policy is not blindly mirroring trust
- QTF and package routing still behave as expected
- EXT promotion requests behave like explicit boundaries instead of silent promotion
- messy mixed-signal scenarios still land in understandable outcomes

## Path 3: Live Local Console

Start the HTTP bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Then open:

- `http://127.0.0.1:8765/alpha/console`
- `http://127.0.0.1:8765/alpha/showcase`
- `http://127.0.0.1:8765/alpha/spawn`

In another shell, ask for a human-readable summary:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

This is the fastest way to see how QTMoS wants to explain itself to a person instead of only to the event bus.

Use `/alpha/showcase` when you want all three built-in showcase stories rendered side-by-side with both summary cards and raw report text for screenshots or teaching.

Use `/alpha/spawn` when you want a multi-lane prompt room: one shared question, an automated local Codex lane, manual browser lanes, generated cross-exam prompts, and a final foldback verdict.

If you want that room to open like a Linux app:

```bash
cd "/path/to/QTMoS-Alp-Beta"
./hosts/install-spawn-desktop.sh
```

That creates a `QTMoS Spawn` launcher in your applications menu and points it at the local Spawn shell.

## Path 4: Browser-Surface Binding

Load the unpacked extension from:

- `bridges/browser-observer/chrome`

Then:

1. start `serve-http`
2. open a known page in Chrome or Chromium
3. make that surface active
4. run `python3 -m bridges.alpha.cli report`

What you are looking for:

- surface and page titles that line up
- a browser origin in the report
- a trust summary that reflects the bind

## Path 5: Package Action Into Containment

If you have the QTF dependencies available, try a local package action:

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

What you are looking for:

- a package install observation in the report
- a QTF route and execution record
- a policy decision that still waits for EXT before allowing a clean local package back to host

Then request the promotion explicitly:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-ext \
  --qtf-label pkg-npm-install-local-demo \
  --package-name local-demo \
  --package-manager npm \
  --reason "Requesting promotion after inspection"
```

What you are looking for next:

- an `EXT:` line in the report
- a policy answer that reflects the package source and the matched QTF evidence
- a clearer difference between containment success and promotion permission

## Path 6: Host Session Breadcrumb

Emit a session breadcrumb manually:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-host-session --stage gnome-handoff --recovery-hint observe_only
```

Then check the report:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

What you are looking for:

- the host session section
- the recovery hint
- the breadcrumb preserved in rebuilt state

## Path 7: Privilege Boundary

Record a privilege-boundary breadcrumb:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli observe-privilege \
  --method sudo \
  --result prompted \
  --target-user root \
  --reason "Testing the sudo boundary" \
  -- /usr/bin/apt install curl
```

Then check the report:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

What you are looking for:

- the privilege line in the report
- the recorded command and target user
- stronger friction when host-session suspicion and privilege escalation line up

## What To Notice

If QTMoS is doing its job, the interesting part is not just whether a command passed.

The interesting part is whether the story still makes sense when signals disagree.

Examples:

- trusted browser state with review-worthy package policy
- suspicious session context preserved even after later clean signals
- containment evidence visible without pretending containment alone proves safety
