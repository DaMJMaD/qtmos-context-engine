# Contributing To QTMoS

Thanks for taking a look at QTMoS.

This project is still Alpha, which means the most valuable contributions are not always giant code drops. A sharp bug report, a confusing README note, a failed setup attempt, or a skeptical security question can be just as useful.

## Good Ways To Help

- run the validation packs and report anything unclear or surprising
- try the local console and say what made sense immediately and what did not
- test on a different machine or desktop setup and report what drifted
- open issues for trust/policy cases that feel wrong, too weak, or too aggressive
- suggest clearer wording where the project sounds more mystical than technical

## Before You Open An Issue

Please sanitize anything personal or machine-specific first.

Good things to remove or replace:

- home directory paths
- usernames
- hostnames
- boot IDs
- tokens
- local share paths

If a raw file is too sensitive to share, a short summary is completely fine.

## Helpful Issue Content

The best reports usually include:

- what you were trying to do
- what you expected QTMoS to say or do
- what it actually said or did
- the command you ran
- a trimmed report output or screenshot if relevant

## Quick Local Check

If you want a fast sanity check before filing something:

```bash
cd "/path/to/QTMoS-Alp-Beta"
python3 -m bridges.alpha.cli validate-browser
python3 -m bridges.alpha.cli validate-policy
python3 -m bridges.alpha.cli validate-package
python3 -m bridges.alpha.cli validate-qtf
python3 -m bridges.alpha.cli validate-host-session
python3 -m bridges.alpha.cli validate-messy
```

## Project Tone

QTMoS is trying to be serious about security without turning into fearware, lockout software, or mystical hand-waving.

The best contributions help keep it:

- local-first
- explainable
- conservative about claims
- useful at risky boundaries
- readable by normal humans
