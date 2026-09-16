# Minimalizer 2.0 Calibration 05 Phase K

## Purpose

Phase K begins exact-result performance optimization after the Phase J profiling baseline.
The rule is strict: optimize one measured hotspot at a time and accept the patch only when canonical output is unchanged.

This phase targets the facet rendering gate, which consumed `8.97%` of the Phase J five-case wall time.
No visual thresholds, palette rules, Region Merge costs, SLIC settings, contour guards, or facet acceptance criteria are changed.

## Optimization

The facet gate previously generated the same planar overlay mask twice for a viable candidate:
1. once for overlay shape-quality checks;
2. again when applying the trial overlay image.

Phase K computes that immutable mask once and passes it to both consumers.
`apply_planar_facet_overlay()` now optionally accepts a precomputed mask and validates that its shape matches the image.
The original no-mask API remains supported and produces the same result.

A focused regression test compares direct overlay application with the precomputed-mask path pixel-for-pixel.
## Exact-result proof

A detached worktree at Phase J handoff commit `006b52877a27d427f6420555a2f6db6230a4f3e4` was compared with the Phase K working tree across all 18 canonical cases.

Results:
- algorithm digest: `18 / 18` identical
- rendered pixel SHA-256: `18 / 18` identical
- deterministic PNG SHA-256: `18 / 18` identical
- accepted facet region IDs: `18 / 18` identical
- full comparison JSON: exact match

The six rendered-facet cases and their accepted counts remain unchanged:
- Koganei-Niko: `1`
- Shishiro-Botan: `2`
- Shiori-Novella: `1`
- Hakos-Baelz: `5`
- Gigi-Murin: `1`
- Aki-Rosenthal: `1`

All other canonical cases remain at zero accepted facets.
## Performance result

The Phase J canonical five-case/two-repeat baseline reported:
- mean wall time: `5.885143 s`
- mean `minimal.facet_gate`: `0.527660 s`

The same profiler after mask reuse reported:
- mean wall time: `5.878943 s`
- mean `minimal.facet_gate`: `0.492390 s`

The targeted facet-gate phase improved by approximately `6.68%`.
Whole-pipeline wall time changed by approximately `-0.11%`, which is small enough to treat as measurement-noise scale rather than a migration-level speedup.

The purpose of this patch is therefore not a large headline speedup. It establishes the Phase K optimization discipline: remove provably redundant work without changing a single canonical output decision.

Canonical comparison artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_K_PERFORMANCE.json`.

## Regression

Focused facet/performance tests: `12 passed` before the final suite.
V2 suite: `131 passed`.
Full repository: `467 passed, 2 failed, 1 warning`.
The two full-repository failures are the pre-existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Phase K.

## Decision

Adopt the facet-mask reuse optimization.
It is an exact-result change with a measurable reduction in the targeted hotspot and zero canonical output drift.

The migration-readiness `performance_budget` blocker remains open because the whole V2 pipeline is still far slower than the legacy baseline measured in Phase I.

## Next engineering step

Proceed to Phase L: Exact-Result Performance Optimization II.
Choose the next measured hotspot only after inspecting exact-result opportunities. Prefer preprocessing numeric scaffolding or another repeated immutable computation before considering algorithmic changes.

Every Phase L candidate must preserve:
- canonical algorithm digest
- rendered pixel and PNG hashes
- facet decisions
- hard invariants
- visual thresholds and preset semantics

Do not switch the legacy default, change calibration thresholds, merge, deploy, or run paid GitHub Actions as part of that step.
