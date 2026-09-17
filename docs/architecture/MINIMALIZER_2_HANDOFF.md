# Minimalizer 2.0 Handoff

Updated: 2026-09-17
Purpose: canonical restart document for the next ChatGPT development chat.

## Start here

Repository: `watarionn/Minimalizer`
Current local RDC branch: `feature/minimalizer-2-calibration-05-phase-u`
Latest committed local gate: `cf2104b` (`Stage Calibration 05 default migration cutover gate`)
Current remote feature branch: `feature/minimalizer-2-calibration-05-planar-polygonization`
Remote feature branch HEAD: `5bce1a9b4b9c765c65b2c78df0bd37a0ad5dee3` (`Record Calibration 05 Phase T handoff`)
Current uncommitted engineering state: Calibration 05 Phase X Default Migration implemented and regression-verified locally.

This is feature-branch work. It is NOT merged to `main` and no PR was created for Phase U-X.
Do not push, create a PR, merge, deploy, or touch `main` unless the user explicitly approves that step.

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
11. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_D.md`
12. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_E.md`
13. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_F.md`
14. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_G.md`
15. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_H.md`
16. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_I.md`
17. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_J.md`
18. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_J_PERFORMANCE.json`
19. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_K.md`
20. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_K_PERFORMANCE.json`
21. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_L.md`
22. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_L_PERFORMANCE.json`
23. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_M.md`
24. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_M_PERFORMANCE.json`
25. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_N.md`
26. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_N_PERFORMANCE.json`
27. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_O.md`
28. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_O_PERFORMANCE.json`
29. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_O_READINESS.json`
30. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_P.md`
31. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_P_COMPATIBILITY.json`
32. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_P_READINESS.json`
33. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_Q.md`
34. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_Q_OUTPUT_FORMAT.json`
35. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_Q_READINESS.json`
36. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_R.md`
37. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_R_ALPHA_BACKGROUND.json`
38. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_R_READINESS.json`
39. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_S.md`
40. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_S_BROWSER_MIGRATION.json`
41. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_S_READINESS.json`
42. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_T.md`
43. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_T_PERFORMANCE.json`
44. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_T_READINESS.json`
45. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_U.md`
46. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_U_RC.json`
47. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_V.md`
48. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_W.md`
49. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_W_CUTOVER_PLAN.json`
50. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_X.md`
51. `docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_X_DEFAULT_MIGRATION.json`
52. This file: `docs/architecture/MINIMALIZER_2_HANDOFF.md`

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
Calibration 05 Phase D engineering commit: `0b2486bfa8be62b5d500bab191793908559831f8`
Calibration 05 Phase E engineering commit: `57a752051598e42e8562b8b22219f5e8b7e35254`
Calibration 05 Phase F engineering commit: `57d47d33d6616c2bb01ecee77463e14bdd044d57`
Calibration 05 Phase G engineering commit: `aba56cd779f8a080a4bea092c3acc967175a9987`
Calibration 05 Phase H engineering commit: `53f1961bd627c4bfdda4695de105f3c14fe58c68`
Calibration 05 Phase I engineering commit: `cbcb660b826256b4f332edefa44ecaf54e0c9a3d`
Calibration 05 Phase J engineering commit: `e68e4476bcf3912bf3709dd417a6d50cc02b3250`
Calibration 05 Phase K engineering commit: `f852f6c8d7e32e9ed4e2e4df8ca85101127466cd`
Calibration 05 Phase L engineering commit: `9cea8cc5886f7acc03f7488d7e2ba4451483697a`
Calibration 05 Phase M engineering commit: `be7cc7f2e4d60639126c5cf8279bf43c95ccda74`
Calibration 05 Phase N engineering commit: `139b868dc34b3acf320f25b8ecb7e81a66b80b89`
Calibration 05 Phase P engineering commit: `5af7fc517d72f97f75c20d0657e949660b52ad76`
Calibration 05 Phase Q engineering commit: `897c7759d76e2c49e9276b35c758d017e963da7f`
Calibration 05 Phase R engineering commit: `84fc96e6c324f5511a7fcaa1716f16bd15597f99`
Calibration 05 Phase S engineering commit: `cbc6885ab87909236bfe9b6ad4763394a7c92de3`
Calibration 05 Phase T engineering commit: `89e81934862c804618d33727f11ea13d3e2ad3af`

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

Latest canonical 18-case run after Calibration 05 Phase H: hard invariant failures `0 / 18`.
Latest V2 regression after Calibration 05 Phase X: `171 passed, 334 deselected, 1 warning`.
Latest full repository regression after Calibration 05 Phase X: `503 passed, 2 failed, 1 warning`.
Latest Default Migration focused suite: `49 passed, 1 warning`.
Latest Phase N exact-output comparison: algorithm digest, pixel SHA, PNG SHA, and accepted facet region IDs all `18 / 18` identical; comparison JSON exact match. Raw SLICO labels also matched `36 / 36` across 18 cases and initial/retry region sizes.
Phase T migration-readiness state remains `ready_for_default=true`, `0` blockers. Phase X has now executed the approved browser cutover locally: browser rollout state is `v2_standard_default`, eligible Standard browser PNG requests use V2, and incompatible/specialized routes remain legacy.
Latest 18-case Phase H visual regression: hard invariant failures `0 / 18`.

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

Calibration 05 Phase D adds a first-class planar-facet candidate stage after Detail Budget.

Calibration 05 Phase E adds a conservative rendering gate and `SceneModel.facet_overlays`.

Calibration 05 Phase F adds a visual shape-quality guard and promotes accepted overlays to the default V2 raster rendering path. `include_facets=False` remains an explicit Phase E baseline opt-out.

Calibration 05 Phase G adds the stable V2 PNG export contract `minimalizer-v2-png-v1`. Repeated export bytes and metadata matched `18 / 18`, exported pixels matched the Phase F canonical final images `18 / 18`, and the regression algorithm digest now includes facet overlays.

Calibration 05 Phase H adds explicit opt-in legacy-boundary integration only: `minimalize_file_png()`, `/api/v2/info`, `/api/v2/minimalize`, and CLI `--v2-shadow-png`. Existing `/api/minimalize`, `/api/info`, browser UI, and normal CLI outputs remain legacy-default.

Calibration 05 Phase I adds a machine-readable migration-readiness gate. It currently reports `ready_for_default=false` with six blockers; quality, deterministic PNG export, and opt-in entry-point integration are ready, while compatibility and performance remain blockers.

Calibration 05 Phase J adds observational performance instrumentation only. Five-case/two-repeat mean V2 wall time is `5.885 s`; the top six costs are oversegmentation `29.46%`, Region Merge `17.57%`, contour `12.93%`, preprocessing `11.69%`, palette `9.64%`, and facet gate `8.97%`. Profiling preserves `algorithm_digest`.

Calibration 05 Phase K reuses the exact same facet overlay mask for shape checking and trial rendering. Canonical digest, pixel SHA, PNG SHA, and accepted facet IDs match Phase J `18 / 18`; the targeted facet-gate phase improved by about `6.68%`.

Calibration 05 Phase L removes full `RegionStats` candidate construction from `geometry_cost()` when only the merged hull area is needed. The same hull helper and cost formula are preserved. Phase K vs Phase L canonical outputs match `18 / 18`; same-machine five-case/two-repeat timing improved Region Merge by about `24.33%` and whole V2 wall time by about `4.72%`.

Calibration 05 Phase M reuses the already-computed pairwise CIEDE2000 matrix during palette hierarchy merge evaluation instead of recomputing representative-color distance for every candidate. Phase L vs Phase M canonical outputs match `18 / 18`; same-machine five-case/two-repeat timing improved palette by about `27.20%` and whole V2 wall time by about `2.98%`.

Calibration 05 Phase N groups SLICO pixel positions once per iteration with a stable sort instead of rescanning the full label image for every cluster. Raw SLICO labels match `36 / 36` across the canonical corpus initial/retry region sizes, and final canonical outputs match Phase M `18 / 18`; same-machine timing improved oversegmentation by about `63.92%` and whole V2 wall time by about `23.34%`.

Calibration 05 Phase O is a post-optimization reassessment only. Service-level V2 mean latency improved from Phase I `5.954 s` to `4.451 s` while legacy remained about `0.74 s`; mean V2/legacy ratio narrowed from `8.28x` to `6.21x`. The Phase O readiness snapshot reported six blockers.

Calibration 05 Phase P adds an exhaustive machine-readable public-control compatibility matrix. Web/CLI mapping ambiguity is resolved conservatively with `2` mapped, `58` legacy-retained, `0` deprecated, and `6` out-of-scope controls. `web_control_mapping` and `cli_control_mapping` are now ready; the migration gate has `4` remaining blockers.

Calibration 05 Phase Q adds a versioned output-format routing contract. PNG is V2-capable under the deterministic PNG contract, while SVG and WEBP remain on the established legacy renderers. `output_format_parity` is now ready; the migration gate has `3` remaining blockers.

Calibration 05 Phase R adds a conservative alpha/background routing contract. Only opaque + white-background requests are V2-native; transparency, source/custom/transparent backgrounds, and ignore-alpha semantics remain on legacy. `alpha_background_parity` is now ready; the migration gate has `2` remaining blockers.

Calibration 05 Phase S adds an explicit browser rollout/rollback contract with `legacy_default`, `v2_standard_opt_in`, and `v2_standard_default` states. Rinka Reference and Color Strip stay pinned to legacy; Phase Q/R eligibility is composed rather than duplicated; rollback is a routing-state change with no data migration. `browser_ui_migration` is now ready.

Calibration 05 Phase T defines and passes the versioned performance/resource budget under the hosted `400 / 1 worker / 2 slots` envelope. Formal five-case/two-repeat results are mean V2 `4.383244 s`, slowest V2 case `4.626395 s`, mean ratio `6.098657x`, max ratio `7.485155x`; all nine checks passed. `performance_budget` is ready and migration readiness reports `ready_for_default=true` with zero blockers.

Calibration 05 Phase U performs the release-candidate dry run without changing production routing. Focused migration tests, V2 regression, rollback behavior, and known full-suite failures were verified locally.

Calibration 05 Phase V passes the final pre-cutover gate. The candidate `v2_standard_default` routing preserves SVG, alpha/background compatibility, specialized-mode legacy pinning, and the no-data-migration rollback target.

Calibration 05 Phase W records the executable cutover package and explicit approval boundary. No remote publish or deployment occurs in Phase W.

Calibration 05 Phase X executes the approved Default Migration locally. The browser Standard one-click path now previews PNG and identifies itself with `X-Minimalizer-Browser-Default: v2`; only default level-4, white-background, opaque, non-custom Standard PNG requests route to V2. Direct `/api/minimalize` callers without the browser marker remain legacy-routed. SVG, transparency-sensitive requests, custom `colors`/`max_shapes`, Rinka Reference, and Color Strip remain legacy. The hosted V2 default keeps the Phase T `analysis_max_side <= 400` envelope, and V2 errors are not silently retried through legacy.

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

Phase X Default Migration is complete locally and all new migration regressions are green.
The next engineering step is **Phase Y: Post-Cutover Acceptance / Release Preparation**.

Phase Y should:
- perform browser-level acceptance against the local migrated route using representative opaque Standard PNG inputs
- confirm user-visible route metadata and download behavior for both V2 and legacy compatibility paths
- recheck rollback by temporarily exercising `legacy_default` in tests without changing canonical rollout state
- package the final release/PR notes and exact rollback instructions
- avoid changing visual thresholds, SLIC targets, Region Merge costs, facet acceptance, or V2 preset semantics

Do not push, create a PR, merge, or deploy until separately approved. GitHub Actions must not be intentionally triggered if they can incur metered cost.

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

Expected local state after the Phase X commit:
branch `feature/minimalizer-2-calibration-05-phase-u`
working tree clean
browser rollout contract `v2_standard_default`
remote feature branch still `feature/minimalizer-2-calibration-05-planar-polygonization` at `5bce1a9b4b9c765c65b2c78df0bd37a0ad5dee3` unless a later publish step was explicitly approved.

Then verify GitHub and read this handoff plus the Phase T-U-V-W-X documents and their JSON snapshots before continuing.

Suggested first user-facing statement in the next chat:
`Calibration 05 Phase X のDefault Migration確定状態をGitHub/RDCで確認してから、Phase Y（Post-Cutover Acceptance / Release Preparation）を開始します。`

## Current merge state

Calibration 01-04 and Calibration 05 Phase A-X remain feature-branch work. Nothing here is merged to `main`.
No PR has been created for Calibration 05 Phase U-X, and Phase X has not been pushed remotely.
The CI workflow is configured for pull requests and pushes to `main`; do not intentionally trigger GitHub Actions when doing so could incur metered cost.
