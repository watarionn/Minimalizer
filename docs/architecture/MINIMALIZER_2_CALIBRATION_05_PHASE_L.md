# Minimalizer 2.0 Calibration 05 Phase L

## Purpose

Phase L continues exact-result performance optimization after Phase K.
The rule remains strict: reduce measured redundant work only when canonical output is unchanged.

Phase L targets Region Merge, which remained the second-largest Phase J hotspot.
No visual thresholds, SLIC targets, Region Merge weights or costs, facet acceptance criteria,
palette semantics, contour guards, or legacy defaults are changed.

## Optimization

`geometry_cost()` previously called `merge_region_stats()` for every evaluated merge candidate.
That built a complete candidate `RegionStats`, including accumulator combination,
annotation/support merging, semantic propagation, readonly copies, and validation.

The geometry cost calculation only consumes the merged convex-hull area.
Phase L therefore calls the same existing `_merged_hull()` helper directly and uses only its area.
The hull algorithm and the geometry-cost formula are unchanged.

A focused regression test compares the optimized geometry cost against the previous
full-`RegionStats` reference calculation exactly.

## Exact-result proof

A detached worktree at Phase K handoff commit
`ef247f21fb61bc46564c8e780be160607fbf341f` was compared with the Phase L working tree
across all 18 canonical cases.
Results:
- algorithm digest: `18 / 18` identical
- rendered pixel SHA-256: `18 / 18` identical
- deterministic PNG SHA-256: `18 / 18` identical
- accepted facet region IDs: `18 / 18` identical
- full comparison JSON: exact match

The focused Region Merge cost suite passed `15 / 15` before the final suites.

## Performance result

Same-machine five-case/two-repeat Phase K baseline:
- mean wall time: `5.898851 s`
- mean `region_merge`: `1.035114 s`

Phase L candidate:
- mean wall time: `5.620624 s`
- mean `region_merge`: `0.783249 s`

Measured changes:
- `region_merge`: approximately `24.33%` faster
- whole V2 wall time: approximately `4.72%` faster

The optimization removes object construction and validation that was provably irrelevant
to the geometry-cost result. It does not approximate, reorder, or alter any cost decision.

Canonical performance artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_L_PERFORMANCE.json`.

## Regression

V2 suite: `132 passed`.
This is Phase K's `131 passed` plus the new geometry-cost exact-reference test.

Full repository: `468 passed, 2 failed, 1 warning`.
The two failures remain the pre-existing missing-asset failures for
`tests/assets/false_face_phase85.png` and are unrelated to Phase L.

## Decision

Adopt the hull-only Region Merge geometry-cost optimization.
It preserves all canonical output evidence while materially reducing the targeted hotspot.

The migration-readiness performance blocker remains open because the full V2 pipeline
still requires further optimization before any legacy-default migration decision.

## Next engineering step

Proceed to Phase M only as another exact-result optimization step.
Re-profile the remaining hotspots and prefer repeated immutable computation or redundant
allocation before any algorithmic change. Oversegmentation, contour, preprocessing,
palette, and the remaining facet-gate work are candidates for inspection, not permission
to change their thresholds or semantics.

Do not switch the legacy default, merge, deploy, or run paid GitHub Actions as part of that step.
