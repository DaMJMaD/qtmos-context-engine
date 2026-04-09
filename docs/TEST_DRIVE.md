# QTMoS Test Drive

This is the quickest way to get a feel for QTMoS without wiring every observer lane on day one.

## Path 1: Zero-Setup Trust And Policy Sanity Check

Run the built-in validation packs:

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

What this proves:

- the trust model is internally coherent
- policy is not blindly mirroring trust
- QTF and package routing still behave as expected
- messy mixed-signal scenarios still land in understandable outcomes

## Path 2: Live Local Console

Start the HTTP bridge:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli serve-http
```

Then open:

- `http://127.0.0.1:8765/alpha/console`

In another shell, ask for a human-readable summary:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli report
```

This is the fastest way to see how QTMoS wants to explain itself to a person instead of only to the event bus.

## Path 3: Browser-Surface Binding

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

## Path 4: Package Action Into Containment

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
- a policy decision that matches the source and containment evidence

## Path 5: Host Session Breadcrumb

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

## Path 6: Privilege Boundary

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
