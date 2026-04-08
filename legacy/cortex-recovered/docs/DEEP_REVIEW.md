# Deep Review

This folder is the result of a full duplicate-lineage review across the five roots the project was split across.

## Root-by-root read

### `/home/dave/Desktop/DavesD2R`

This branch held the strongest leader orchestration:

- richer `Step1Leader.ahk`
- slot-based leader handoff
- stronger window/path resolution
- better marker detection and capture loop

Its body files are an older divergent branch.

### `/home/dave/Desktop/Davesflow`

This branch held the strongest follower runtime:

- much larger `Step2Follower.ahk`
- driver input/output lane
- follower profiles
- richer sync logic
- Step3/AI-era control work

Its modular body files match the stable branch found in `David's Working AHK`.

### `/home/dave/Desktop/David's Working AHK`

This branch held the strongest QTMoS-facing bridge pieces:

- `QTMoSSharedSync.ahk`
- `QTMoSPolicyHook.ahk`
- newest `MindsEye.ahk`

It also shares the same stable modular body-file branch as `Davesflow`.

### `/home/dave/Desktop/QTMoSV1dev`

This is the stronger QTMoS Python/operator lineage compared to the duplicate under `UniProjects`.

It appears to be the newer source for:

- `qtmos_boot.py`
- `qtmos_storage.py`
- `systems modulation`

### `/home/dave/Desktop/UniProjects`

This contains older duplicate QTMoS and systems-modulation trees. It was reviewed for lineage, but it was not the strongest source for the recovered package here.

## What won and why

### Leader

Winner: `DavesD2R/Daves Play Buddies/Step1Leader.ahk`

Why:

- best leader identity handling
- best slot/path mapping
- best leader handoff behavior
- stronger capture/marker loop than the other copies

### Follower

Winner: `Davesflow/Daves Play Buddies/Step2Follower.ahk`

Why:

- clearly newest and richest follower logic
- retains the driver/profile infrastructure
- stronger than both the short `David's Working AHK` copy and the older `DavesD2R` copy

### Shared AHK bridge

Winner: `David's Working AHK/Daves Play Buddies`

Why:

- only branch with QTMoS shared sync and policy hook
- newest `MindsEye.ahk`
- already aligned with the newer Alpha-style shared seam

### Body files

Winner: `Davesflow` / `David's Working AHK` shared branch

Why:

- hash-identical across the stable modular set
- clearly the newer body branch than `DavesD2R`

## Important correction from the source architecture

`IdentifyThyself.txt` and `IdentifyThyBody.txt` are not accidental duplicates. They are mirrored on purpose because one role can hold a file open while the other still needs independent access.

That is why the recovered package stores them under separate role folders instead of keeping same-folder doubles.

## Result

The recovered package is not a blind copy of one branch. It is a stitched strongest-lineage build:

- leader from `DavesD2R`
- follower from `Davesflow`
- shared sync/hook/context from `David's Working AHK`
- stable body cortex from the shared modular branch

The pathing was then repaired so it can live in one explicit location under Alp-Beta instead of depending on the old fractured folders.
