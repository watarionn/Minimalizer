# Minimalizer 2.0 Handoff

Updated: 2026-09-15
Purpose: canonical restart document for the next ChatGPT development chat.

## Start here

Repository: `watarionn/Minimalizer`
Current branch: `feature/minimalizer-2-calibration-03-contour-micro-cleanup`
Current HEAD: `6989b2741ea581dd307008142d872ae1eb60d60d`
Commit message: `Calibrate Minimalizer 2 weak contour corners`

This branch is pushed to origin. It is NOT merged to `main` and no PR was created.
Do not merge, deploy, or touch `main` unless the user explicitly approves that step.

Local RDC clone:
`C:\Users\watar\AppData\Local\Temp\minimalizer_phase1_verify`

## Canonical design documents

1. `docs/architecture/MINIMALIZER_2_ARCHITECTURE_SPEC_V1.md`
2. `docs/architecture/MINIMALIZER_2_PHASE10_CLOSURE.md`
3. `docs/architecture/MINIMALIZER_2_CALIBRATION_01.md`
4. `docs/architecture/MINIMALIZER_2_CALIBRATION_02.md`
5. `docs/architecture/MINIMALIZER_2_CALIBRATION_03.md`
6. This file: `docs/architecture/MINIMALIZER_2_HANDOFF.md`

## Architecture status

Minimalizer 2.0 is a non-AI visual decomposition engine:
`pixel -> micro structure -> superpixel/region -> merged region -> primitive`.

Core pipeline is implemented through Phase X:
Source -> SLICO -> Region Adjacency Graph -> Region Merge Tree -> Nested Hierarchy Cut -> Shared Boundary Contour -> Primitive Fitting -> Palette Consolidation -> Coverage-safe Detail Budget -> Scene Model.

Important invariant: all presets share one Region Merge Tree. Presets must not rerun Region Merge.
`RAG` in this project means Region Adjacency Graph, not Retrieval-Augmented Generation.

Phase X Closure commit: `2499b3a09f61fbbe1ee2ad049473b8d552cdb00c`
Calibration 01 commit: `9f357e54f22f9f3be9a2194375b420e6df1f81c6`
Calibration 02 commit: `e05dafdca122d2fe622bd28ccf69b01936f53e40`
Calibration 03 commit: `6989b2741ea581dd307008142d872ae1eb60d60d`

## Calibration results so far

Closure mean visual groups: `48.278`
Calibration 01 mean visual groups: `41.944`
Calibration 02 mean visual groups: `37.167`
Calibration 03 keeps the same visual-group range and safely reduces weak contour vertices.

Calibration 03, 18-case result:
- hard invariant failures: `0 / 18`
- vertices: `102,508 -> 102,291`
- vertex reduction: `217` (`0.212%`)
- cases with fewer vertices: `18 / 18`
- Contour IoU changed: `0 / 18`
- max directional loss changed: `0 / 18`

## Regression status

Latest V2 regression after Calibration 03: `104 passed`.
Latest full repository regression after Calibration 03: `436 passed, 2 failed, 1 warning`.

The two known failures are pre-existing and caused only by the missing asset:
`tests/assets/false_face_phase85.png`

Affected tests:
- `tests/test_character_face_geometry.py::test_rejected_face_skips_face_geometry_quality`
- `tests/test_character_quality_retry.py::test_rejected_face_is_not_penalized_as_missing_face`

Do not attribute these two failures to Minimalizer 2.0 changes unless the missing asset is restored and the tests still fail.

## Canonical 18-case corpus

Manifest:
`tests/assets/approved18_manifest.json`

RDC source images:
`C:\Users\watar\Documents\GitHub\Minimalizer-phase10-subject-segmentation\examples\phase14_user18_input`

All 18 source SHA-256 values were rechecked against the manifest during Calibration 02 and matched.

Google Drive Minimalizer root folder:
`1Fore4mo1NOxCOFP_SjgbThUV87K-p-Mj`

Google Drive Approved Geometric Reference folder:
`1oWUtdUAfLE4x8_T5VS5GQyHEHn7FQ35v`
Folder name: `採用見本_幾何学ミニマル_20260911`

## Current Calibration 03 behavior

Minimal preset uses:
- `strong_corner_threshold = 0.65` for normal presets
- `minimal_strong_corner_threshold = 0.6525` for Minimal only

The stronger probes were intentionally rejected:
- `0.655` begins to worsen directional loss on Hakos-Baelz
- `0.66+` begins to reduce Contour IoU on some cases
- `0.70` was clearly too aggressive, e.g. Kobo-Kanaeru IoU dropped near the guard

The accepted implementation changes only weak corner anchoring in the shared boundary graph. It does not post-warp one side of a shared boundary.

## Recommended next engineering step

Proceed to `Calibration 04`.
Goal: reduce medium-size accessory / clothing detail that still exceeds the Approved Reference style, while preserving the large face/hair/torso/arm/outfit masses.

Start with measurement, not a threshold guess:
1. Verify RDC branch/head/status and GitHub remote branch first.
2. Read Calibration 02 and 03 docs.
3. Identify medium-size retained regions after Detail Budget, especially accessory/clothing fragments.
4. Probe conservative area/importance bands on smoke cases first.
5. Reuse existing anchor, relationship, coverage, and target-min guards.
6. Run the canonical 18-case corpus before accepting a change.
7. Require hard invariant failures = 0.
8. Run V2 regression and full repository regression.

Do not reopen Region Merge unless evidence proves a later-stage solution cannot solve the problem.

## Operational rules for the next chat

GitHub cost rule: do not run GitHub Actions or any metered workflow that may create `net_amount > 0`. Use RDC/local validation first.

Git workflow:
- never commit directly to `main`
- work branch -> validate locally -> push feature branch
- PR / Ready for review / merge require the appropriate explicit user approval
- `次の工程へ` authorizes only the next engineering step, not merge/deploy
- never force-push or directly update `main` refs without explicit approval

Trust rule: before saying GitHub or RDC is unavailable, explicitly explore the connected resource/tool.

## Exact restart checklist

Run these first on RDC:
`git branch --show-current`
`git rev-parse HEAD`
`git status --short`

Expected clean state at this handoff:
branch `feature/minimalizer-2-calibration-03-contour-micro-cleanup`
HEAD `6989b2741ea581dd307008142d872ae1eb60d60d`

Then verify the same remote branch on GitHub and read this handoff file plus `MINIMALIZER_2_CALIBRATION_03.md`.

Suggested first user-facing statement in the next chat:
`Calibration 03 の完了状態をGitHub/RDCで確認してから、Calibration 04（中サイズのアクセサリー・衣装ディテール整理）を再開します。`

## Current merge state

Calibration 01, 02, and 03 are feature-branch work. The current Calibration 03 branch is pushed but not merged to `main`.
GitHub Actions for commit `6989b2741ea581dd307008142d872ae1eb60d60d` were confirmed as zero runs.
