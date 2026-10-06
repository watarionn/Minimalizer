# SA8 Palette Role Adapter GC001 Visual Gate — 2026-10-07

Status: **ARCHITECTURE PASS / VISUAL CANDIDATE HOLD / RENDERER PROMOTION REVERTED**

## Scope

Evaluate the SA8 Palette Role Adapter production-candidate bridge on real GC001 using the canonical source and Phase 4 masks.

Production inference used:
- GC001 source pixels;
- canonical Phase 4 semantic masks;
- canonical structural graph;
- deterministic SA8 palette-role/component adapter;
- deterministic SA8 candidate bridge;
- existing semantic render guard;
- SA7.38 face raster guard.

Golden and Browser fallback v12 were evaluation-only and never production inputs.

## Fresh GC001 result

Canonical SA7.35 hard gate:
- Feature Survival: PASS
- required signatures: 16
- missing: 0
- Forbidden Face Detail: 0.00%
- hard gate: PASS

Face raster guard:
- face pixels: 4,937
- changed outside face: 0
- observed fill RGB: [250, 225, 218]

Visual delta:
- vs adopted Silhouette Proportion Recomposition: 31.4394%
- vs SA7.44 HOLD candidate: 84.4092%

Same-run evaluation-only Lab distance to Rinka Golden:
- SA8 candidate: 92.8560
- SA7.44 candidate: 51.4763
- Browser fallback v12: 33.4426

These three Lab values are only compared within this fresh run; they are not copied from older stage reports.

Interpretation:
SA8 clears the hard safety gate and creates a substantial visual change, but it is a clear visual regression against the existing evaluation floor. The multi-component palette-role architecture is useful; the current direct renderer promotion is not.

Decision: **HOLD**

## Production decision

Keep:
- `palette_role_adapter.py`
- multi-component palette-role IR
- SA7.30 compatibility path without largest-component collapse
- `palette_role_candidates.py`
- palette-role budget / primitive budget separation
- source-only candidate bridge and its tests

Do not keep active:
- direct replacement of the canonical renderer's established `major_color_masses()` pass with SA8 candidates.

The renderer connection from PR #191 is reverted after this real-image gate. The bridge remains available for the next bounded visual experiment.

## Process correction

Mistake:
PR #191 merged the renderer connection before the required real GC001 four-way/regression-floor review.

Cause:
the synthetic/full regression suite was treated as sufficient for the connection step even though the project rule requires actual visual comparison before merging a meaningful visual stage.

Impact:
a hard-gate-safe but visually regressive renderer path briefly reached main.

Fix:
fresh GC001 evaluation was run immediately; the result is HOLD; the renderer promotion is reverted while preserving the reusable SA8 IR/bridge.

Prevention:
future visual-authority promotions must follow:
1. branch implementation;
2. focused/full regression;
3. real GC001 candidate;
4. fresh canonical hard gate;
5. actual regression-floor comparison;
6. only then merge production renderer activation.

## Evidence preservation

Google Drive canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA8_20261007_HOLD`

Folder ID:
`1-m_TytOmWEIrlzVdHBIa5srCMKZ1N5xk`

Verified evaluation JSON:
- `GC001_sa8_eval.json`
- Drive ID: `1FkvCYSfbL4r9xov6t2iILASWLujcCCxU`

The local execution workspace also produced:
- `GC001_sa8_final.png`
- `GC001_sa8_rendered_before_face.png`
- `GC001_sa8_palette_candidate.svg`

Those visual artifacts were copied into the mounted canonical Drive path. The evaluation JSON was additionally uploaded and read through the Drive API path as the authoritative machine-readable record.

## Next

Do not abandon SA8.

Next experiment should use the SA8 bridge selectively rather than wholesale replacing the established major-color layer. Candidate directions:
- retain established dominant mass authority;
- use SA8 disconnected components only for source-supported secondary fields that would otherwise be lost;
- bound additional primitive cost globally;
- require per-role coverage gain before promotion;
- rerun GC001 before any renderer activation merge.
