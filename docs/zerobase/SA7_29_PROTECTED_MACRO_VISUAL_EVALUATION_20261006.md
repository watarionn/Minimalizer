# SA7.29 Protected Macro Visual Evaluation — 2026-10-06

Status: EVALUATION COMPLETE / VISUAL REJECT

SA7.29 evaluated the merged SA7.26-SA7.28 semantic macro path on GC001 with protected identity accents recomposed above macro hair/clothing masses.

## Hard gates
- Visual Delta vs adopted Silhouette Proportion baseline: 30.0398% — PASS (>=1.5%)
- Source-supported Feature Survival: 16/16, missing=0 — PASS
- Forbidden Facial Detail: 0.00% — PASS
- Structural / Topology validation: PASS
- Anatomy validation: PASS
- Face Neutralization: PASS
- Protected identity accents recomposed: YES
- Candidate primitive count: 15

## Browser fallback v12 regression floor
Evaluation references only; neither v12 nor Golden enters production generation.

At common 340x340 evaluation resolution:
- candidate -> Golden LAB mean absolute distance: 54.8153
- Browser fallback v12 -> Golden LAB mean absolute distance: 16.1205
- candidate edge density: 0.03148
- v12 edge density: 0.04046

The candidate changes substantially and becomes geometrically simpler, but the change is not a visual improvement over the v12 regression floor. Its coarse macro replacement discards too much palette/compositional structure. Therefore Visual Delta PASS is not sufficient for adoption.

## Decision
REJECT SA7.29 as a visual version.
- Do not update the adopted visual baseline.
- Do not append SA7.29 to accepted Minimalizer Version History.
- Keep current adopted visual baseline at `a60aaa12ff22c2f6384a598442964710ce939d87`.
- Keep SA7.26-SA7.28 architecture merged because its semantic-role replacement and protected-foreground contracts passed regression independently of this rejected visual candidate.

## Next
SA7.30 should add palette-role and composition-aware macro subdivision before rendering. The goal is not more contour detail. It is to preserve a small number of dominant internal color/garment masses while retaining semantic simplification.

Drive evidence:
`GC001_IMG_1205/Semantic_Abstraction/SA7_29_20261006_REJECTED_VISUAL/`
contains the candidate, gate report, and actual four-way comparison.
