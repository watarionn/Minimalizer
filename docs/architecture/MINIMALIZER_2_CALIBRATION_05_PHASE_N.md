# Minimalizer 2.0 Calibration 05 Phase N

## Purpose

Phase N continues exact-result performance optimization after Phase M.
The constraint remains strict: remove redundant work only when image-producing behavior is unchanged.

This phase targets SLICO center updates inside oversegmentation.
No visual threshold, SLIC target, retry rule, distance formula, center formula, Region Merge cost, palette rule, or facet acceptance criterion is changed.

## Observation

After each SLICO assignment iteration, the implementation updated every cluster by evaluating `labels == cluster_id` separately.
On a representative canonical case this created about 9,760 full-image cluster masks across the initial and retry segmentations.

Every mask selected pixels in C-order, then computed the same Lab mean, coordinate means, and maximum color-distance scale.
The repeated whole-image scans were lookup work rather than algorithm semantics.

## Optimization

Phase N groups flat pixel positions once per SLICO iteration with a stable sort of the label map.
Stable ordering preserves the exact C-order previously produced by boolean masking for each cluster.

The grouped positions are reused for Lab samples and X/Y coordinate samples.
All mean calculations, color-scale calculations, assignment distances, iteration counts, region sizes, and retry decisions remain unchanged.

## Exact-result proof

Before modifying production code, the candidate SLICO updater was compared against the Phase M implementation.
Across all 18 canonical cases, both the initial region size and retry region size were checked.
Raw SLICO label maps matched exactly `36 / 36`.

A detached worktree at Phase M handoff commit `5e7faec7fd376aabcfa97033fdcf28887a60b3dd` was then compared with the Phase N candidate across all 18 canonical cases.

Results:
- algorithm digest: `18 / 18` identical
- rendered pixel SHA-256: `18 / 18` identical
- deterministic PNG SHA-256: `18 / 18` identical
- accepted facet region IDs: `18 / 18` identical
- comparison JSON: exact match

A focused regression fixture also pins the exact raw SLICO label SHA-256 for a deterministic two-mass image.

## Performance result

Same-machine five-case/two-repeat Phase M baseline:
- mean wall time: `5.747478 s`
- mean `oversegmentation`: `1.983030 s`

Same profiler after stable cluster-position grouping:
- mean wall time: `4.405856 s`
- mean `oversegmentation`: `0.715427 s`

Changes:
- targeted oversegmentation phase: approximately `63.92%` faster
- whole V2 pipeline wall time: approximately `23.34%` faster

Canonical performance artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_N_PERFORMANCE.json`.

## Regression

Focused segmentation tests: `8 passed`.
V2 suite: `134 passed`.
Full repository: `470 passed, 2 failed, 1 warning`.

The two full-repository failures remain the pre-existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Phase N.

## Decision

Adopt stable cluster-position grouping.
It removes repeated full-image cluster scans while preserving the exact pixel order used by SLICO center updates.
The canonical segmentation, hierarchy, palette, facet decisions, rendered pixels, and deterministic PNG bytes remain unchanged.

## Next engineering step

Proceed to Phase O as a post-optimization performance and migration-readiness reassessment before choosing another optimization target.
Re-profile the Phase N pipeline and compare current V2 service-level performance with the Phase I migration evidence.
Do not invent a migration SLA or switch defaults.
Compatibility blockers must still be handled explicitly even if the performance gap has narrowed.
