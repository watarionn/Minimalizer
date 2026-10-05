# SA7.13 Multi-Holdout Eyewear Generalization — 2026-10-05

Status: GENERALIZATION FAIL / DINO CONTRASTIVE V1 NOT AUTHORIZED

## Frozen gate
Worst-case positive-vs-negative margin >= 0.05, with at least two positive and two negative holdouts. Source SHA-256 is mandatory.

## Holdout set
Positive:
- Sorashina Sopia: 0.0420649
- Shiranui Flare: 0.0326921

Negative:
- AZKi: -0.0004598
- Gawr Gura: -0.0044693
- Ceres Fauna: -0.0282032
- Nanashi Mumei: -0.0147748

Worst positive: 0.0326921
Worst negative: -0.0004598
Margin: 0.0331519
Required: 0.05
Result: FAIL.

All reference files were selected and preserved before scoring. GC001 was not used in this stage.

## Decision
Do not lower the 0.05 gate. Do not tune the contrastive bank on GC001. SA7.12 DINO contrastive v1 is not sufficiently general to act as an independent semantic witness and is removed from the promotion path.

SA7.9 region evidence remains observer evidence only. SA7.5 structural remains fail-closed. Renderer stays disconnected.

## Next
SA7.14 should investigate a geometry-first independent witness rather than another GC001-tuned DINO threshold: paired lens/frame topology, symmetry, bridge continuity, or a separately trained/frozen eyewear detector evaluated on non-target multi-holdout first.
