# SA7.42 Multi-Component Background Field Geometry — 2026-10-06

Status: IMPLEMENTATION PASS / CANONICAL HARD GATE PASS / VISUAL ADOPTION HOLD

SA7.42 is the first production synthesis of the visual-abstraction precedent plan.

It fixes the SA7.41 root cause: palette-cluster count and rendered-field count were incorrectly coupled because each palette cluster retained only its largest connected component.

## Precedent synthesis

SA7.42 adopts a production-safe subset of external precedent ideas:

- LIVE:
  one source palette role may contribute multiple disconnected source-supported layers/components.
- AdaVec:
  palette-role complexity and geometry/render-field budget are separate concepts.
- Primitive / Geometrize:
  eligible components are selected under a bounded global field budget using deterministic source-supported ranking.
- CLIPascene:
  simplicity remains a first-class constraint; small fragments are not kept merely because they exist.

No external model becomes production semantic/render authority.

## Production contract

Background extraction is now:

Source border-connected background
-> source palette clusters
-> all connected components per retained cluster
-> existing component eligibility/safety guards
-> deterministic global candidate ranking
-> bounded rendered background fields
-> canonical background scene

Hard constraints remain:

- max source palette clusters: 3
- max rendered background fields: 6
- minimum field ratio: 3%
- source coverage >= existing contract
- expansion <= existing contract
- subject overlap = 0
- deterministic extraction/order
- source-only palette authority
- no Golden/v12 production input

Stable per-field identity now includes:
- cluster_index
- component_index

Background scene provenance now records:
- background_palette_cluster_count
- background_component_count
- background_generated_count

The historical reporting ambiguity between retained source pixels and rendered polygon area was also corrected by reporting:
- retained_area
- render_area
separately.

## GC001 canonical result

SA7.42 found 5 safe rendered background fields across 2 palette clusters.

### Orange cluster

1. dominant component
   - source area: 23,451 px
   - retained: 23,156 px
   - source coverage: 0.98742
   - expansion: 1.00674
   - subject overlap: 0
   - vertices: 37

2. recovered major disconnected component
   - source area: 5,058 px
   - retained: 4,963 px
   - source coverage: 0.98122
   - expansion: 0.99170
   - subject overlap: 0
   - vertices: 10

3. recovered major disconnected component
   - source area: 3,919 px
   - retained: 3,808 px
   - source coverage: 0.97168
   - expansion: 0.97397
   - subject overlap: 0
   - vertices: 6

### Red cluster

1. dominant component
   - source area: 16,778 px
   - retained: 16,674 px
   - source coverage: 0.99380
   - expansion: 1.02032
   - subject overlap: 0
   - vertices: 29

2. recovered major disconnected component
   - source area: 3,882 px
   - retained: 3,828 px
   - source coverage: 0.98609
   - expansion: 1.02550
   - subject overlap: 0
   - vertices: 7

This recovers the three major omitted fields diagnosed by SA7.41 without lowering the 3% threshold or promoting tiny black/sub-threshold fragments.

## Canonical hard gate

Fresh SA7.35 evaluation on the final SA7.42 candidate:

- required source-supported signatures: 16
- Feature Survival: missing=0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- overall canonical hard gate: PASS
- face guard changed pixels outside semantic face mask: 0

Golden raster provenance in production scene:
- false

## Visual evidence

- visual delta vs adopted baseline: 82.1445%
- pixel delta vs SA7.39: 10.7673%
- SA7.39 -> Golden LAB MAE: 32.4133
- SA7.42 -> Golden LAB MAE: 25.2943
- Browser fallback v12 -> Golden LAB MAE: 16.2422

The actual four-way review confirms that SA7.42 materially restores missing red/orange background composition and removes large white omissions from SA7.39.

However, the current subject reconstruction remains visibly weaker than Browser fallback v12. Therefore the v12 regression floor is not beaten.

Decision:
- merge the generic multi-component background implementation;
- preserve SA7.42 as an architectural/background quality improvement;
- keep visual adoption HOLD;
- do not update the adopted visual baseline;
- do not append SA7.42 to accepted Minimalizer Version History.

## Verification

Focused:
- SA7.33 + SA7.34 + SA7.42 background tests: 14/14 PASS

Full:
- ZeroBase: 631/631 PASS
- Python compileall: PASS
- git diff --check: PASS

## Drive preservation

Folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_42_20261006_HOLD`

Folder ID:
`1bothhAkj3rIOlQhX3CJFMKxueA9iTNtj`

Verified cloud files:

- `GC001_sa742_canonical_multifield_scene.svg`
  - ID `1d9VQPbGEGoJ2c_RZU8zDz_FfewW71en4`
- `GC001_sa742_rendered_before_face.png`
  - ID `1la0Yl5aOXuPKJKPR9o8nE1mWoxMgbEdN`
- `GC001_sa742_final.png`
  - ID `1cDIFiYGK-UH1836flSSL8b2v0XXtTgZw`
- `GC001_sa742_scene_report.json`
  - ID `1xHKjYaZjUpm6NE1_Y06e6VbZVMG1wcW9`
- `GC001_sa742_gate_report.json`
  - ID `1x0CP-QGeQGxzSVyibA9WftUkjeFEa3Ir`
- `GC001_sa742_eval.json`
  - ID `1Ekn7Dw9Ug1Cka-e7-VT7MBMpqVOWwFmy`
- `GC001_comparison_4way_sa742_hold_20261006.png`
  - ID `1a_ZoLOcpYKYLa-_QTTX06DQz8Rx-hjz1`

## Next

SA7.43 Adaptive Primitive Budget.

Use the AdaVec-inspired architecture already recorded in:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Goal:
move from fixed per-role/per-stage primitive counts toward deterministic source-supported adaptive budgets while preserving hard global caps and all existing semantic safety gates.
