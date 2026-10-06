# SA7 Geometry Re-authoring Closeout / Integration Gate — 2026-10-06

Status: SA7 COMPLETE / POST-SA7 PB2 NEXT

Canonical repository: watarionn/Minimalizer
Verified main before closeout docs:
`85af2d9e304d20cf89577d0f1ddb33a423b11e26`

## Purpose

Close SA7 Geometry Re-authoring after the precedent-assimilation sequence SA7.42-SA7.47 and hand control to the adopted Post-SA7 Precedent Backport Pass beginning with PB2 / SA2 Evidence Adapter.

This closeout adds no new production geometry behavior.

## Completed SA7 sequence

### SA7.42 Multi-Component Background Field Geometry

Classification:
**PRODUCTION IMPLEMENTED / VISUAL CANDIDATE HOLD**

Primary precedents:
- LIVE
- AdaVec
- Primitive / Geometrize
- CLIPascene simplicity objective

Result:
- palette-cluster count separated from rendered-field count
- one palette role may own multiple disconnected fields
- deterministic global field budget
- three major omitted GC001 background components recovered
- subject overlap remained zero
- Feature Survival missing=0
- Forbidden Face Detail=0.00%

Merge:
`e6f464c53a924655e1f6dfd84a19ffcc4a09d63b`

### SA7.43 Adaptive Primitive Budget

Classification:
**PRODUCTION IMPLEMENTED / VISUAL CANDIDATE HOLD**

Primary precedent:
- AdaVec

Result:
- fixed hair=3 / clothing=2 role capacities replaced with global source-supported macro budget
- required minima reserved first
- optional budget competes in one global source-support frame
- unused budget may remain unused
- GC001: hair=1, major_clothing=3, unused=1

Merge:
`217c9c366661735a3d01d1352e5bb23ab0dbaacb`

### SA7.44 Layer-wise Residual Re-authoring

Classification:
**PRODUCTION IMPLEMENTED / VISUAL CANDIDATE HOLD**

Primary precedents:
- LIVE
- SuperSVG
- Primitive
- Geometrize

Result:
- SA7.43 coarse geometry remains base authority
- source-supported missing residuals receive a separate bounded residual budget
- marginal value rewards role coverage gain and taxes geometry complexity
- GC001: 5 candidates, 3 selected clothing residuals
- all selected authority spill = 0
- Feature Survival missing=0
- Forbidden Face Detail=0.00%
- Golden LAB improved 25.286020 -> 25.275946

Merge:
`8abe4bbbd32f4e8cb2bead0f6a340e7faeb88feb`

This is the latest SA7 stage that changes the rendered GC001 candidate.

### SA7.45 Semantic Retention Observer

Classification:
**OBSERVER-ONLY IMPLEMENTED**

Primary precedents:
- CLIPasso
- CLIPascene

Result:
- model-agnostic semantic-retention report
- global / patch / optional role-local semantic evidence
- optional fidelity / simplicity separation
- observer unavailable does not alter production
- observer cannot override hard failures
- real cached DINOv3 runtime verified
- SA7.43 -> SA7.44 retention: 0.729017 -> 0.729867

Merge:
`015551fbdcca9114a10bbdd001f970e6d3f2e0f9`

### SA7.46 Primitive-Type Advisor Research

Classification:
**ADVISOR-ONLY IMPLEMENTED / PRODUCTION NO-OP**

Primary precedent:
- StarVector

Result:
- validated primitive-family suggestion schema
- deterministic source-geometry evidence baseline
- advisor/source agreement audit
- unsupported or authoritative suggestions fail closed
- advisor output never production-eligible in SA7.46
- local StarVector runtime/model not present; no new heavy install performed
- GC001 source evidence classified all eight inspected roles as polygon
- production promotion count = 0

Merge:
`cc38323274546970a16c9ab0d233f85b0417bcc7`

### SA7.47 Layer / Occlusion Evidence Research

Classification:
**OBSERVER-ONLY IMPLEMENTED / PRODUCTION NO-OP**

Primary precedents:
- LayerPeeler
- SuperSVG

Result:
- deterministic pairwise OVERLAP / TOUCHING / DISJOINT graph
- source overlap never invents front/behind direction
- existing canonical z-order may be observed but never changed
- GC001: 28 relations
  - OVERLAP: 1
  - TOUCHING: 13
  - DISJOINT: 14
- dominant overlap hair/head = 12,421 px
- production output changed = false

Merge:
`85af2d9e304d20cf89577d0f1ddb33a423b11e26`

## Integrated safety state

The SA7 sequence preserves the following non-negotiable contracts:

- no generative img2img / fill / inpainting / missing-content redraw
- Golden and Browser fallback v12 remain evaluation-only
- no GC001-specific production coordinates/colors/masks
- Feature Survival missing=0 remains hard
- Forbidden Face Detail=0.00% remains hard
- face raster safety remains authoritative
- anatomy/topology authority is not replaced by observers
- source coverage / expansion / spill guards remain hard
- observer/advisor scores cannot rescue hard failures
- production geometry remains deterministic
- unsupported external-model availability does not change production output

## Final main verification

Verified on exact main:
`85af2d9e304d20cf89577d0f1ddb33a423b11e26`

Results:
- ZeroBase: **678/678 PASS**
- Python compileall: **PASS**
- git diff --check: **PASS**

## Visual state at SA7 closeout

Latest rendered SA7 candidate:
- SA7.44 GC001 HOLD

Latest adopted visual baseline remains:
`a60aaa12ff22c2f6384a598442964710ce939d87`
Silhouette Proportion Recomposition

Reason:
- SA7.42-SA7.44 materially improved architecture and selected visual details
- SA7.45-SA7.47 add observer/advisor evidence only
- Browser fallback v12 still remains substantially closer to the desired overall subject representation
- therefore no SA7.42-SA7.47 candidate is promoted as the adopted visual baseline

This is not a failure of SA7 closeout.
SA7 closes on a verified geometry/evidence architecture while visual-quality improvement continues through the backport and later SA8-SA10 sequence.

## Preserve

Canonical SA7 reports:
- `SA7_42_MULTI_COMPONENT_BACKGROUND_FIELD_GEOMETRY_20261006.md`
- `SA7_43_ADAPTIVE_PRIMITIVE_BUDGET_20261006.md`
- `SA7_44_LAYER_WISE_RESIDUAL_REAUTHORING_20261006.md`
- `SA7_45_SEMANTIC_RETENTION_OBSERVER_20261006.md`
- `SA7_46_PRIMITIVE_TYPE_ADVISOR_RESEARCH_20261006.md`
- `SA7_47_LAYER_OCCLUSION_EVIDENCE_RESEARCH_20261006.md`

All stage-specific GC001 visual/observer evidence was preserved under:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/`

## Next

Per the adopted execution-order decision, **do not proceed directly to SA8**.

Canonical next phase:

**PB2 / SA2 Evidence Adapter Backport**

Use:
- SuperSVG
- LayerPeeler
- LIVE

Goal:
backport the region/layer/disconnected-component/occlusion evidence learned during SA7 into the original SA2 Evidence Adapter boundary while preserving observer provenance and existing production authority.

After PB2:
PB3 -> PB4 -> PB5 -> PB6 -> PB7 review -> SA8 -> SA9 -> SA10.
