# HND-20261006 Minimalizer SA7.42 Multi-Component Background Field Geometry Handoff

Date: 2026-10-06
Status: SA7.42 COMPLETE / SUPERSEDED BY SA7.43 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now a completed SA7.42 historical record. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-sa743-adaptive-primitive-budget-next.md`.

Latest completed behavior/evaluation stage before this handoff:
- SA7.41 commit: `a36d7602f22d045677ac5e38ac1429dc9b2b500e`

Latest adopted visual baseline remains:
- `a60aaa12ff22c2f6384a598442964710ce939d87`
- Silhouette Proportion Recomposition

Do not treat SA7.29 / SA7.33 / SA7.34 / SA7.37 / SA7.38 / SA7.39 HOLD candidates as adopted visual baselines.

## Non-negotiable rules

- No generative img2img / fill / inpainting / missing-content redraw.
- Golden and Browser fallback v12 are evaluation-only, never production inference inputs.
- Do not hard-code GC001 colors, coordinates, masks, or missing signatures into production.
- Every visual candidate must run the canonical SA7.35 hard gate fresh from the candidate image.
- Feature Survival must remain missing=0.
- Forbidden Face Detail must remain 0.00%.
- Browser fallback v12 remains the visual regression floor.
- Actual four-way comparison is required for visual acceptance.
- HOLD/REJECT stages must not be added to accepted Minimalizer Version History.

## Completed path to this handoff

### SA7.38 Face Neutralization Path Reconciliation — COMPLETE

Canonical face safety is restored.

Production contract:
- deterministic post-render face raster safety guard
- geometry authority from the source-derived semantic face mask
- face color selected from actually observed source face pixels
- zero pixels outside the face mask may change
- no Golden/adopted-baseline pixels as repair authority

Fresh canonical hard gate on the combined candidate:
- Feature Survival: missing=0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- overall canonical hard gate: PASS

Visual adoption remained HOLD.

Canonical record:
`docs/zerobase/SA7_38_FACE_NEUTRALIZATION_RECONCILIATION_20261006.md`

### SA7.39 Required Semantic Mass Canonical Integration — COMPLETE

The SA7.37 research-only reservation overlay dependency was removed.

Required semantic masses are integrated into the canonical VectorScene with source-only authority and protected-role guards.

Fresh canonical hard gate:
- Feature Survival: missing=0 — PASS
- Forbidden Face Detail: 0.0000% — PASS

SA7.39 commit:
`091acb48e2957fef7954245ddf81a8d91808e198`

Canonical record:
`docs/zerobase/SA7_39_REQUIRED_SEMANTIC_MASS_CANONICAL_INTEGRATION_20261006.md`

### SA7.40 Remaining Gap Re-attribution — COMPLETE

Role-local Golden-gap attribution was rerun on the SA7.39 final candidate.

Largest remaining contributions:
1. background_complement — 0.09093
2. hair — 0.04331
3. head — 0.03837
4. lower_body — 0.03069

The next visual target was confirmed as source-only background representation.

SA7.40 commit:
`bd0f98837b4b13d4b74946799d85f48a8f50e247`

Canonical record:
`docs/zerobase/SA7_40_REMAINING_GAP_REATTRIBUTION_20261006.md`

### SA7.41 Background Residual Field Attribution — COMPLETE

The remaining background gap was decomposed using source-derived Lab palette clustering and connected components.

Root cause:
SA7.33 conflated palette-cluster count with output-field count by retaining only the largest connected component from each palette cluster.

Major omitted source-supported components:

Orange cluster:
- 5,058 px, bbox [0,171,73,134], safe polygon
- 3,891 px, bbox [0,0,105,59], safe polygon

Red cluster:
- 3,913 px, bbox [165,0,118,97], safe polygon

Do not lower the existing 3% minimum field-ratio threshold.
Do not promote the tiny black cluster.
The 266 px orange component remains below the existing field-ratio contract and stays omitted.

SA7.41 commit:
`a36d7602f22d045677ac5e38ac1429dc9b2b500e`

Canonical record:
`docs/zerobase/SA7_41_BACKGROUND_RESIDUAL_FIELD_ATTRIBUTION_20261006.md`


## Precedent assimilation plan

The external visual-abstraction precedents are intentionally mapped across SA2-SA10 rather than treated as SA7.42-only tricks.

Canonical plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Immediate SA7.42 synthesis:
- LIVE: multiple disconnected source-supported components may remain separate layers
- AdaVec: palette-cluster count and rendered-field/geometry budget are separate
- Primitive / Geometrize: bounded marginal-value candidate selection under hard guards
- CLIPascene: simplicity remains an explicit objective, so not every source fragment should survive

Deferred/backported homes:
- SuperSVG / LayerPeeler -> SA2 evidence/layer decomposition
- CLIPasso / CLIPascene -> SA3/SA9/SA10 semantic-retention observer/evaluation
- StarVector -> SA7 primitive-type advisor research only
- AdaVec / LIVE / Primitive / Geometrize -> broader SA7 geometry re-authoring
- AdaVec / LIVE / LayerPeeler -> SA8 palette/layer role separation

Do not broadly reopen completed stages. Preserve their contracts and add focused observer/schema backports or later SA7.x stages.

## SA7.42 Multi-Component Background Field Geometry — COMPLETE

Goal:
allow one source palette cluster to contribute multiple major disconnected background fields without weakening existing semantic safety guards.

Required contract:
- keep at most three source palette clusters
- allow multiple major connected components per retained cluster
- preserve minimum field ratio >= 3%
- preserve source-coverage guard
- preserve expansion guard
- preserve zero subject-overlap guard
- bound the global rendered background-field count separately from palette-cluster count
- deterministic extraction and ordering
- source-only production authority
- no Golden coordinates/colors as production inputs

Initial GC001 target:
- retain the already-rendered dominant orange/red components
- additionally represent the three major omitted safe components identified in SA7.41
- do not include the tiny black fragments or sub-threshold 266 px orange fragment

## SA7.42 completion result

Implementation:
- PR #177
- merge SHA: `e6f464c53a924655e1f6dfd84a19ffcc4a09d63b`
- canonical report: `docs/zerobase/SA7_42_MULTI_COMPONENT_BACKGROUND_FIELD_GEOMETRY_20261006.md`

Verification:
- focused background tests: 14/14 PASS
- ZeroBase: 631/631 PASS
- compileall: PASS
- git diff --check: PASS
- fresh SA7.35 hard gate: Feature Survival missing=0, Forbidden Face Detail=0.00%, PASS
- actual four-way reviewed
- visual adoption: HOLD because Browser fallback v12 remains stronger overall

Drive preservation:
- folder: `SA7_42_20261006_HOLD`
- folder ID: `1bothhAkj3rIOlQhX3CJFMKxueA9iTNtj`

SA7.42 recovered all three major background components diagnosed in SA7.41 while preserving the existing 3% threshold and zero subject overlap.

## Historical implementation order

1. Create a fresh SA7.42 branch/worktree from current main.
2. Refactor background extraction so palette clusters and connected output fields are separate concepts.
3. Add a global field-count bound independent of palette-cluster count.
4. Add focused synthetic tests for:
   - two disconnected major components from one palette cluster
   - sub-threshold component rejection
   - subject-overlap rejection
   - deterministic ordering
   - global field bound
5. Generate the GC001 canonical scene candidate.
6. Run fresh SA7.35 canonical hard gate.
7. Require:
   - Feature Survival missing=0
   - Forbidden Face Detail 0.00%
   - zero subject-overlap violations
8. Run full ZeroBase and relevant regressions.
9. Generate actual four-way:
   Source | Browser fallback v12 | current | Rinka Golden.
10. Compare against the v12 visual regression floor.
11. Preserve artifacts and update this handoff/current pointer.

## Current state declaration

SA7.42 is complete. The canonical continuation point is:

**SA7.43 Adaptive Primitive Budget**

Current handoff: `docs/handoffs/HND-20261006-sa743-adaptive-primitive-budget-next.md`.
