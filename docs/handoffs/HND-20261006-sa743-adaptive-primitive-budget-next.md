# HND-20261006 Minimalizer SA7.43 Adaptive Primitive Budget Handoff

Date: 2026-10-06
Status: SA7.42 COMPLETE / SA7.43 NEXT
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

Restart from current `main`.

SA7.42 implementation merge:
- PR #177
- merge SHA: `e6f464c53a924655e1f6dfd84a19ffcc4a09d63b`

SA7.42 canonical record:
`docs/zerobase/SA7_42_MULTI_COMPONENT_BACKGROUND_FIELD_GEOMETRY_20261006.md`

Precedent assimilation plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Latest adopted visual baseline remains:
- `a60aaa12ff22c2f6384a598442964710ce939d87`
- Silhouette Proportion Recomposition

SA7.42 is merged as a generic architectural/background improvement, but visual adoption remains HOLD because Browser fallback v12 still wins the overall visual regression-floor review.

## SA7.42 closure

SA7.42 decoupled source palette-cluster count from rendered background-field count.

Production result:
- max palette clusters and max rendered fields are separate budgets;
- one retained palette role may own multiple disconnected components;
- component identity is stable through `cluster_index` + `component_index`;
- minimum field ratio remains 3%;
- source coverage, expansion, and zero subject-overlap guards remain hard requirements;
- source pixels remain palette authority;
- Golden/v12 remain evaluation-only;
- deterministic global field selection is bounded.

GC001:
- 5 safe background fields across 2 palette clusters;
- all three major omitted fields identified by SA7.41 were recovered;
- all subject overlaps = 0;
- Feature Survival missing=0 PASS;
- Forbidden Face Detail=0.00% PASS;
- canonical hard gate PASS;
- Golden LAB MAE improved 32.4133 -> 25.2943;
- v12 remains 16.2422, so visual adoption HOLD.

Verification:
- focused background suite: 14/14 PASS
- ZeroBase: 631/631 PASS
- compileall: PASS
- git diff --check: PASS
- actual four-way reviewed

Drive:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_42_20261006_HOLD`

Folder ID:
`1bothhAkj3rIOlQhX3CJFMKxueA9iTNtj`

## SA7.43 Adaptive Primitive Budget — NEXT

### Goal

Replace rigid per-role / per-stage primitive counts with deterministic source-supported adaptive budgets, while retaining strict global caps and all existing semantic safety gates.

This is the AdaVec-inspired next step from the precedent assimilation plan.

The objective is not "more primitives". It is to spend geometry where the source actually needs it and keep simple regions simple.

### Design principles

1. Separate semantic importance from geometric complexity.
   - a required semantic role must survive even if geometrically simple;
   - a visually complex source region may receive more geometry only inside its authorized role.

2. Budget from source evidence only.
   Candidate evidence may include:
   - component count;
   - contour complexity;
   - source-supported area;
   - residual shape complexity;
   - structural/semantic importance already present in the Semantic Abstraction path.

3. Preserve hard caps.
   Adaptive allocation may redistribute budget, but cannot create an unbounded primitive count.

4. Fail closed.
   Insufficient budget for required structure must not silently delete a required role.

5. Keep production deterministic and explainable.
   No CLIP/VLM/model score may directly own the production budget in SA7.43.

6. Preserve existing guards:
   - Feature Survival missing=0;
   - Forbidden Face Detail=0.00%;
   - anatomy/topology;
   - source coverage;
   - expansion;
   - role/subject spill protection;
   - Golden/v12 evaluation-only boundary.

### Preferred implementation order

1. Inventory all fixed primitive/geometry budget constants used by the current canonical Semantic Abstraction path.
2. Define an explicit `AdaptivePrimitiveBudget` result with:
   - role/component identity;
   - required minimum;
   - allocated budget;
   - hard maximum;
   - source-evidence reasons.
3. Implement deterministic source-only complexity scoring.
4. Reserve required minima first, then distribute remaining global budget.
5. Add synthetic tests:
   - simple role receives minimum budget;
   - complex source-supported role receives more budget;
   - required role cannot be starved by optional complexity;
   - total never exceeds global cap;
   - reorder invariance / deterministic rerun;
   - unsupported micro-fragments do not inflate budget.
6. Connect behind the current canonical semantic geometry path without removing the old safe fallback.
7. Evaluate GC001 with fresh SA7.35 hard gate.
8. Run full ZeroBase and relevant regressions.
9. Generate actual four-way and compare to v12.
10. Preserve all evidence before any visual adoption decision.

## Deferred precedent stages

After SA7.43, current research queue remains:
- SA7.44 Layer-wise Residual Re-authoring: LIVE / SuperSVG / Primitive / Geometrize
- SA7.45 Semantic Retention Observer: CLIPasso / CLIPascene
- SA7.46 Primitive-Type Advisor Research: StarVector
- SA7.47 Layer / Occlusion Evidence Research: LayerPeeler / SuperSVG

These names are planning anchors, not permission to skip validation or force implementation if SA7.43 evidence points elsewhere.

## Non-negotiable boundaries

- No generative img2img / fill / inpainting / missing-content redraw.
- Golden and Browser fallback v12 are evaluation-only.
- No GC001-specific production colors, coordinates, masks, or heuristics.
- No model/VLM becomes runtime geometry authority without a later explicit promotion decision.
- Do not weaken a hard safety gate to improve aggregate visual metrics.
- Do not change the adopted visual baseline until actual four-way review beats the v12 regression floor.

## Current state declaration

The canonical continuation point is:

**SA7.43 Adaptive Primitive Budget**
