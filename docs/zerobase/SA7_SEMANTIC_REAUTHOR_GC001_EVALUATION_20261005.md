# SA7 Semantic Geometry Re-authoring GC001 Evaluation — 2026-10-05

Status: REJECTED / DO NOT MERGE VISUAL BEHAVIOR

## Candidate

Branch: `feature/semantic-abstraction-sa7-geometry-v2`

The candidate re-authors semantic masks into bounded geometry:

- face: one plain surface,
- each arm: at most two axis primitives before protected accents,
- hair: at most three coarse masses,
- clothing: bounded major masses,
- source-supported identity accents: bounded late reservations,
- no generative reconstruction and no Golden raster in production inference.

## GC001 result

The first candidate produced a large visual change while preserving face/anatomy safety:

- Visual Delta vs adopted Silhouette Proportion Recomposition: 36.41% PASS
- Forbidden Face Detail: 0.00% PASS
- Anatomy Gate: PASS
- Structural Graph: PASS
- primitive count: 17
- generic Feature Survival: FAIL, missing=4

A generic bounded body identity reservation reduced missing signatures from 4 to 1:

- Visual Delta: 41.14% PASS
- Forbidden Face Detail: 0.00% PASS
- focused geometry tests: 8/8 PASS
- full ZeroBase before the final lower-body probe: 515/515 PASS
- generic Feature Survival: FAIL, missing=1
- remaining missing signature: quantized RGB (80, 144, 208), area ratio 0.005032, lower-body region near normalized (0.6410, 0.8980)

Increasing the lower-body reservation from one to two accents did not recover the remaining signature.
The experiment stops here rather than increasing detail budgets until the gate passes.

## Decision

REJECT the SA7 visual candidate. Do not merge it into main.

Reason: the hard Feature Survival gate outranks Visual Delta and aggregate visual change. The candidate
demonstrates that semantic geometry re-authoring can create a substantial simplification, but the current
generic identity reservation still loses one adopted-baseline feature signature.

## SA7.1 next direction

Do not add more generic accent slots. Instead, introduce semantic-budget-backed survival reservations:

1. derive protected source-supported feature signatures before geometry re-authoring,
2. bind each reservation to an authorized semantic part,
3. reserve the minimum geometry required for required/high-value signatures,
4. let optional/compressible accents compete only for remaining budget,
5. verify that reservations are generic and deterministic on synthetic non-GC001 cases,
6. rerun GC001 with unchanged Feature Survival threshold.

The reservation layer may preserve source evidence but must not use Golden raster, Golden coordinates,
case-specific color constants, or GC001-specific feature names.

## Artifacts

Local evaluation workspace:
`C:\Work\Temp\macro-gc001\semantic_abstraction`

Relevant artifacts:

- `GC001_semantic_reauthor_stage.png`
- `GC001_semantic_reauthor_stage_v2.png`
- `GC001_comparison_4way_semantic_reauthor_20261005.png`
- `GC001_compare_adopted_vs_sa7_20261005.png`
- `GC001_feature_region_review_sa7_20261005.png`
- `GC001_semantic_reauthor_metrics.json`
- `GC001_semantic_reauthor_report.json`
- `GC001_sa7_feature_survival.json`
- `GC001_sa7_v2_gate_report.json`

No visual adoption is claimed by these artifacts.
