# Minimalizer 2.0 Calibration 05 Phase M

## Purpose

Phase M continues exact-result performance optimization after Phase L.
The constraint remains strict: reduce redundant work only when canonical image-producing behavior is unchanged.

This phase targets palette consolidation, which remained one of the larger post-Phase-L costs.
No visual thresholds, SLIC targets, Region Merge costs, contour rules, palette semantics, or facet acceptance criteria are changed.

## Observation

`build_palette_hierarchy()` already computes a complete CIEDE2000 distance matrix between all region representative colors.
Every palette node uses one of those original region colors as its representative color.

Despite that, each hierarchy merge candidate called `ciede2000(first.lab, second.lab)` again while evaluating color cost.
On representative images this meant thousands of repeated scalar CIEDE2000 calculations for values already present in the immutable pairwise matrix.

## Optimization

`evaluate_palette_merge()` now accepts an optional precomputed `color_distance`.
Its existing no-argument behavior is preserved and still computes CIEDE2000 directly.
Within `build_palette_hierarchy()`, candidate evaluation now reads the representative-color distance from the already-computed pairwise distance matrix and supplies it to `evaluate_palette_merge()`.
The color-cost formula itself is unchanged.

A focused regression test verifies both:
- vectorized pairwise CIEDE2000 and direct scalar CIEDE2000 are bit-exact for the tested pair;
- precomputed-distance palette evaluation equals direct evaluation exactly.

## Exact-result proof

A detached worktree at Phase L handoff commit `d2760b1b00eaba040dbad58f700daf1d2c20f449` was compared with the Phase M candidate across all 18 canonical cases.

Results:
- algorithm digest: `18 / 18` identical
- rendered pixel SHA-256: `18 / 18` identical
- deterministic PNG SHA-256: `18 / 18` identical
- accepted facet region IDs: `18 / 18` identical
- comparison JSON: exact match

No canonical palette decision, rendering decision, facet decision, or image byte changed.

## Performance result

Same-machine five-case/two-repeat Phase L baseline:
- mean wall time: `5.608317 s`
- mean `minimal.palette`: `0.569563 s`
Same profiler after pairwise distance reuse:
- mean wall time: `5.441253 s`
- mean `minimal.palette`: `0.414645 s`

Changes:
- targeted palette phase: approximately `27.20%` faster
- whole V2 pipeline wall time: approximately `2.98%` faster

The remaining dominant cost is oversegmentation, followed by Region Merge / contour / preprocessing depending on case and measurement noise.

Canonical performance artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_M_PERFORMANCE.json`.

## Regression

Focused palette tests: `8 passed`.
V2 suite: `133 passed`.
Full repository: `469 passed, 2 failed, 1 warning`.

The two full-repository failures remain the pre-existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Phase M.

## Decision

Adopt pairwise palette-distance reuse.
It removes repeated immutable computation, gives a measurable targeted speedup, and preserves canonical output exactly.

## Next engineering step

Proceed to Phase N only after re-profiling the post-Phase-M pipeline.
Prefer another exact-result opportunity in oversegmentation, contour, or preprocessing if the redundant work is clearly separable from algorithm semantics.

Every Phase N candidate must preserve:
- canonical algorithm digest
- rendered pixel and PNG hashes
- facet decisions
- palette decisions and representative colors
- hard invariants
- all visual thresholds and preset semantics

Do not change SLIC target behavior, Region Merge cost semantics, visual thresholds, facet acceptance criteria, legacy defaults, merge state, or deployment state as part of that step.
