# PB7 / SA7 Precedent Integration Review — 2026-10-07

Status: **REVIEW COMPLETE / NO NEW PROMOTION / SA8 READY**

## Goal

Review PB2-PB6 against SA7.42-SA7.47, remove conceptual duplication, confirm authority boundaries, and decide whether any observer/advisor evidence has enough deterministic proof to be promoted before SA8.

PB7 is intentionally a review stage. It does not add production geometry or create a new visual candidate unless a concrete gap is proven.

## Cross-stage classification

| Stage | Classification | Production effect |
|---|---|---|
| PB2 / SA2 | IMPLEMENTED + OBSERVER-ONLY | none |
| PB3 / SA3 | IMPLEMENTED + OBSERVER/ADVISOR-ONLY | none |
| PB4 / SA4 | IMPLEMENTED + DIAGNOSTIC-ONLY | none |
| PB5 / SA5 | NO-OP-BY-DESIGN + COMPATIBILITY PASS | none |
| PB6 / SA6 | IMPLEMENTED + OBSERVER-ONLY DIAGNOSTIC | none |

All five stages preserve the existing production candidate.

## SA7 geometry-side review

SA7.42 Multi-Component Background Field Geometry:
- production implemented;
- source-supported multi-component fields;
- deterministic field ranking;
- visual candidate remained HOLD.

SA7.43 Adaptive Primitive Budget:
- production implemented;
- source-supported adaptive complexity allocation;
- visual candidate remained HOLD.

SA7.44 Layer-wise Residual Re-authoring:
- production implemented;
- deterministic source-supported residual layers;
- latest SA7 stage that changed the rendered GC001 candidate;
- visual candidate remained HOLD.

SA7.45 Semantic Retention Observer:
- observer-only;
- no production authority.

SA7.46 Primitive-Type Advisor:
- advisor-only;
- no production primitive-selection authority.

SA7.47 Layer/Occlusion Evidence:
- observer-only;
- no production z-order authority.

Conclusion:
the intended geometry-side precedent assimilation is already present. No broad SA7 reimplementation is justified.

## Duplication review

### Relation analysis

PB2 is the canonical lower-layer implementation for:
- connected components;
- OVERLAP / TOUCHING / DISJOINT relations;
- optional canonical z-order observation;
- evidence authority provenance.

SA7.47 consumes the PB2 relation observer rather than duplicating mask analysis.

PB6 also consumes PB2 relation observations and only adds topology compatibility interpretation.

Decision:
**no duplicate relation analyzer remains to remove.**

### Semantic-retention analysis

SA7.45 owns the model-agnostic semantic-retention observer contract.

PB3 consumes semantic-retention reports but does not recompute model similarity.

PB4 renders PB3/PB2 diagnostics but does not recompute policy.

Decision:
**observer, policy diagnostic, and debug presentation remain correctly separated.**

### Face and anatomy authority

PB5 does not replace SA7.38 face raster safety.

PB6 does not replace anatomy/topology hard guards.

Decision:
**hard safety authority remains single-source and canonical.**

## Promotion review

PB7 reviewed every precedent-derived non-production signal for deterministic promotion.

### PB2 structured components and relations

Decision: **NO PROMOTION**

Reason:
component existence and contact/overlap are source observations, not sufficient semantic, topology, z-order, or rendering decisions.

### PB3 importance recommendations

Decision: **NO PROMOTION**

GC001 has 83 structured components, but per-component semantic removal/merge evidence is unavailable. All 83 recommendations therefore remain `insufficient-evidence`.

Area/support alone must not become deletion authority.

### PB4 debug board

Decision: **NO PROMOTION**

PB4 is presentation/audit infrastructure. A debug surface must not become a policy engine.

### PB5 face compatibility

Decision: **NO PROMOTION / NO-OP-BY-DESIGN PRESERVED**

SA7.38 remains the authoritative face raster safety contract.

### PB6 anatomy/occlusion compatibility

Decision: **NO PROMOTION**

GC001 reports:
- SUPPORTING: 2
- POTENTIAL_CONFLICT: 3
- INSUFFICIENT_EVIDENCE: 1
- NEUTRAL: 22

The three potential conflicts are useful diagnostics, but explicitly demonstrate why source mask relations cannot rewrite canonical anatomy/topology.

### SA7.45 semantic retention

Decision: **NO PROMOTION**

Useful as research/evaluation evidence, but not a lone production decision.

### SA7.46 primitive advisor

Decision: **NO PROMOTION**

Advisor runtime was unavailable for the GC001 PB3 audit, and advisor output is not a deterministic production grammar.

### SA7.47 occlusion evidence

Decision: **NO PROMOTION**

Overlap/contact does not prove front/behind. Existing canonical z-order may be observed but not mutated.

## Authority boundary after PB7

Production authority remains with deterministic source-supported rules and existing hard guards.

Observer/advisor evidence may:
- explain;
- diagnose;
- rank research candidates;
- feed later teacher/regression tooling.

Observer/advisor evidence may not:
- rescue hard failures;
- invent missing anatomy;
- clear Forbidden Face Detail;
- mutate canonical topology or z-order;
- choose production geometry alone;
- use Golden/v12 raster/coordinates as production input.

## Hard-gate review

PB2-PB6 records confirm no weakening of:
- Feature Survival;
- face neutralization;
- anatomy;
- topology;
- source authority;
- expansion;
- overlap;
- deterministic production behavior.

The latest PB6 validation passed:
- focused PB6/anatomy/PB2/SA7.47: 36/36;
- full ZeroBase: 734/734;
- compileall: PASS.

Earlier PB2-PB5 focused/full validations are recorded in their canonical closeout documents.

PB7 changes documentation only, so no new production test surface is introduced.

## Precedent map after review

- SuperSVG / LayerPeeler / LIVE observation concepts -> PB2
- CLIPasso / CLIPascene semantic-retention concepts -> SA7.45 + PB3
- StarVector primitive suggestion -> SA7.46 + PB3 advisor context
- inspectability across precedents -> PB4
- face compatibility -> PB5, no production replacement
- anatomy/occlusion compatibility -> PB6, observer-only
- AdaVec / LIVE / Primitive / Geometrize / SuperSVG production geometry synthesis -> SA7.42-SA7.44

No precedent concept requires another SA7 production patch before SA8.

## PB7 classification

**REVIEW COMPLETE / NO NEW PROMOTION / NO-OP-BY-DESIGN CODEWISE**

This is a successful outcome, not a missing implementation.

The backport pass gate is satisfied:
- PB2-PB6 classified;
- changed stages verified;
- hard boundaries preserved;
- provenance inspectable;
- production path deterministic;
- no unjustified observer/advisor promotion remains.

## Next canonical phase

**SA8 / Palette Role Adapter**

SA8 should start from the now-backported evidence stack.

Carry forward:
- palette-cluster identity must remain separate from connected-component identity;
- one palette role may own multiple disconnected fields;
- source pixels remain production palette authority;
- palette-count limits and primitive-count limits remain separate;
- PB2 component evidence may inform diagnostics/structure but cannot silently become production geometry;
- AdaVec / LIVE / LayerPeeler concepts should be integrated from the beginning;
- Golden/v12 remain evaluation-only.
