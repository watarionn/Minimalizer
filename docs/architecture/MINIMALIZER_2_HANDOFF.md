# Minimalizer 2.0 Handoff

Updated: 2026-09-15
Purpose: canonical restart document for the next ChatGPT development chat.

## Start here

Repository: `watarionn/Minimalizer`
Current branch: `feature/minimalizer-2-calibration-05-planar-polygonization`
Current engineering commit: `a5ce9dd22acf8aaeb89a27e1cb5a41d9802cf60f`
Current branch HEAD: verify the remote branch; review/handoff metadata may be later documentation-only commits
Engineering commit message: `Add Calibration 05 macro facet diagnostics`

This is a feature branch. It is NOT merged to `main` and no PR was created.
Do not merge, deploy, or touch `main` unless the user explicitly approves that step.

Local RDC clone:
`C:\Users\watar\AppData\Local\Temp\minimalizer_phase1_verify`

## Canonical design documents

1. `docs/architecture/MINIMALIZER_2_ARCHITECTURE_SPEC_V1.md`
2. `docs/architecture/MINIMALIZER_2_PHASE10_CLOSURE.md`
3. `docs/architecture/MINIMALIZER_2_CALIBRATION_01.md`
4. `docs/architecture/MINIMALIZER_2_CALIBRATION_02.md`
5. `docs/architecture/MINIMALIZER_2_CALIBRATION_03.md`
6. `docs/architecture/MINIMALIZER_2_CALIBRATION_04.md`
7. `docs/architecture/MINIMALIZER_2_POST_CALIBRATION_04_REVIEW.md`
8. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_A.md`
9. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_B.md`
10. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_C.md`
11. This file: `docs/architecture/MINIMALIZER_2_HANDOFF.md`

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
Calibration 04 engineering commit: `dc10ca1e6cd4daf2dddee6af41ca19a53f75188d`
Calibration 05 Phase A engineering commit: `e7b9d5e384182acc84815d6cf52f402cc987fb81`
Calibration 05 Phase B engineering commit: `82e99f5b979a034080fb2ae31de91ff686cca3d3`
Calibration 05 Phase C engineering commit: `a5ce9dd22acf8aaeb89a27e1cb5a41d9802cf60f`

## Calibration results so far

Closure mean visual groups: `48.278`
Calibration 01 mean visual groups: `41.944`
Calibration 02 mean visual groups: `37.167`
Calibration 03 keeps the Calibration 02 visual-group range and safely reduces weak contour vertices.
Calibration 04 mean visual groups: `33.833`.

Calibration 04, direct 18-case comparison against Calibration 03 behavior:
- hard invariant failures: `0 / 18`
- mean visual groups: `37.167 -> 33.833`
- visual-group range: `21..44 -> 21..43`
- additional style collapses: `58`
- cases with fewer visual groups: `15 / 18`
- cases at Minimal `target_min=28`: `3`
- Kikirara-Vivi: `37 -> 31`
- Otonose-Kanade: `34 -> 28`
- Hakos-Baelz: `42 -> 41`

Calibration 04 uses a conservative medium-detail band after the existing micro-detail pass:
- Minimal preset only
- `0.0008 < area_ratio <= 0.0015`
- `importance <= 0.60`
- core coverage geometry remains present; only style collapses
- existing characteristic-anchor, protected relationship, adjacency fallback, and `target_min` guards remain active

Probe `0.0020` was rejected because the 18-case mean would fall to about `31.333` and six cases would reach the lower bound, which was too aggressive for this calibration.

## Regression status

Latest canonical 18-case run after Calibration 04: hard invariant failures `0 / 18`.
Latest V2 regression after Calibration 05 Phase C diagnostics: `111 passed`.
Latest full repository regression after Calibration 05 Phase C diagnostics: `443 passed, 2 failed, 1 warning`.
Latest 18-case Phase C diagnostic visual regression: hard invariant failures `0 / 18`.

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

Google Drive handoff folder:
`1Obe4PsQVh0x4RkWV0wIP1FEcRhVHD-6f` (`00_HANDOFF`)

Google Drive handoff document:
`16pSPtRC2VqFKUaV0tezn8_A7PFcZP-FwXDY2108j1ko`
`https://docs.google.com/document/d/16pSPtRC2VqFKUaV0tezn8_A7PFcZP-FwXDY2108j1ko/edit`

Google Drive Approved Geometric Reference folder:
`1oWUtdUAfLE4x8_T5VS5GQyHEHn7FQ35v`
Folder name: `採用見本_幾何学ミニマル_20260911`

## Current calibration behavior

Calibration 03 remains active for Minimal contour cleanup:
- `strong_corner_threshold = 0.65` for normal presets
- `minimal_strong_corner_threshold = 0.6525` for Minimal only

Calibration 04 adds a second Detail Budget cleanup band after micro-detail cleanup. It does not alter Region Merge, Hierarchy Cut, Contour geometry, Primitive fitting, Palette Consolidation, or coverage geometry.

Calibration 05 Phase B changes Minimal shared-boundary geometry only:
- Minimal no longer hard-splits every pixel-scale strong corner
- junctions/borders/protected relationships remain hard structure
- conservative shared-boundary line-fit is enabled only for Minimal
- line-fit defaults: min points `4`, span `0.03*diag`, max deviation `0.004*diag`, efficiency `0.94`
- every accepted line still passes the existing topology/IoU/directional/intersection guards

Calibration 05 Phase C adds observational macro-facet diagnostics only:
- `macro_facet_count`
- `macro_large_facet_share`
- `macro_mean_vertices`
- production output is unchanged by the diagnostics

## Post-Calibration-04 review result

Approved Reference SHA-256 values matched `18 / 18`, and the comparison run had hard invariant failures `0 / 18`.
Mean current/reference image-metric ratios were:
- edge density: `0.7503`
- long-line support: `0.3155`
- approximate polygon vertices: `1.3825`
- edge-contour count: `0.9483`

Long-line support was lower than the Approved Reference in `18 / 18` cases, and edge density was lower in `18 / 18` cases.
The dominant remaining mismatch is therefore not simply excess detail. Visible boundaries are too locally fragmented, while the Approved References use long straight edges and deliberate large planar facets.

Internal Calibration 04 diagnostics also show mean selected regions `70.89`, mean contour vertices `5696.72`, and polygon share `90.44%`.
Calibration 05 is fixed as **Planar Polygonization / Long-Line Reconstruction**.
Stronger global Detail Budget collapse is specifically not the next step; Todoroki-Hajime is already too flat, while Raora-Panthera demonstrates that important accessory planes must survive.

## Recommended next engineering step

Proceed to Calibration 05 Phase D: Selected-Region Planar Facet Reconstruction.

Phase C established the macro-facet gap with normalized diagnostics:
- mean current/reference facet count: `31.56 / 67.00`
- mean current/reference large-facet area share: `0.8850 / 0.6394`
- mean current/reference vertices per facet: `9.75 / 7.80`
- hard invariant failures: `0 / 18`

Stage decomposition shows Detail Budget contributes only part of the facet loss: Primitive `35.72`, Palette `36.00`, Detail Budget `31.61`, Final `31.56`, Reference `67.00`. A source-color blend probe moved facet count only to `36.33` and left long-line support effectively flat (`0.23525` vs Phase B `0.23542`), so recoloring alone is rejected.

Phase D should use selected-region topology and shared boundaries to build structurally justified planar facet candidates after Detail Budget. Keep Region Merge and Calibration 04 target ranges unchanged initially. Do not add arbitrary shading or per-image special cases. Todoroki-Hajime remains the over-flattening guard; Raora-Panthera and Hakos-Baelz remain structure-preservation guards.

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
branch `feature/minimalizer-2-calibration-05-planar-polygonization`
engineering commit `a5ce9dd22acf8aaeb89a27e1cb5a41d9802cf60f`
branch HEAD may be a later review/documentation commit; verify the remote branch HEAD before work.

Then verify the same remote branch on GitHub and read this handoff file plus `MINIMALIZER_2_CALIBRATION_05_PHASE_A.md`, `MINIMALIZER_2_CALIBRATION_05_PHASE_B.md`, and `MINIMALIZER_2_CALIBRATION_05_PHASE_C.md`.

Suggested first user-facing statement in the next chat:
`Calibration 05 Phase C の確定状態をGitHub/RDCで確認してから、Phase D（Selected-Region Planar Facet Reconstruction）の候補設計と保守的 probe を開始します。`

## Current merge state

Calibration 01, 02, 03, and 04 remain feature-branch work. Calibration 05 Phase A, Phase B, and Phase C are also on the same feature branch. Nothing here is merged to `main`.
No PR has been created for Calibration 05.
The CI workflow is configured for pull requests and pushes to `main`; pushing this feature branch must not intentionally trigger GitHub Actions.
