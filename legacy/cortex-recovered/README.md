# Cortex Recovered

This package is the recovered leader/follower cortex assembled from the fractured copies across:

- `/home/dave/Desktop/DavesD2R`
- `/home/dave/Desktop/Davesflow`
- `/home/dave/Desktop/David's Working AHK`
- `/home/dave/Desktop/QTMoSV1dev`
- `/home/dave/Desktop/UniProjects`

It is laid out by role instead of by accidental duplication:

- `leader/`
- `follower/`
- `shared/`
- `context/`
- `body/`
- `docs/`

## Chosen lineage

- `leader/Step1Leader.ahk` comes from the strongest `DavesD2R` branch.
- `follower/Step2Follower.ahk` comes from the strongest `Davesflow` branch.
- `shared/QTMoSSharedSync.ahk` and `shared/QTMoSPolicyHook.ahk` come from `David's Working AHK`.
- `body/core/` comes from the stable shared modular branch used by both `Davesflow` and `David's Working AHK`.
- `body/top-level/` preserves the older pre-modular body corpus.
- `body/leader/IdentifyThyself.txt` and `body/follower/IdentifyThyBody.txt` are kept separate on purpose for role-safe access.

## Shared root

The recovered scripts now share one explicit root:

- `shared/image directory`
- `shared/runtime`
- `shared/qtmos-share`

That makes the old lock-avoidance mirrors visible and intentional instead of scattered.

## Launch order

1. Run `leader/Step1Leader.ahk`
2. Run `follower/Step2Follower.ahk`
3. Optionally run `context/MindsEye.ahk`
4. Optionally run `shared/QTMoSPolicyHook.ahk`

## Important boundary

This is a recovered Windows/Wine AutoHotkey stack. It has been consolidated and path-fixed here, but it still depends on the original Windows-side D2R/window environment to do real live work.
