# HND-20261006 Minimalizer SA7.45 Semantic Retention Observer Handoff

Date: 2026-10-06
Status: SA7.45 COMPLETE / SUPERSEDED BY SA7.46 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-sa746-primitive-type-advisor-next.md`.

SA7.44 implementation:
- PR #179
- merge SHA: `8abe4bbbd32f4e8cb2bead0f6a340e7faeb88feb`

Canonical SA7.44 record:
`docs/zerobase/SA7_44_LAYER_WISE_RESIDUAL_REAUTHORING_20261006.md`

Cross-phase precedent plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Latest adopted visual baseline remains:
- `a60aaa12ff22c2f6384a598442964710ce939d87`
- Silhouette Proportion Recomposition

SA7.44 implementation is merged, but its GC001 visual candidate remains HOLD because Browser fallback v12 still wins the overall visual regression-floor review.

## SA7.44 closure

SA7.44 added a bounded source-supported residual layer stage above the accepted SA7.43 coarse semantic macro geometry.

GC001:
- residual candidates: 5
- selected residual layers: 3
- selected role: major_clothing
- residual cap: 3
- authority spill: 0 for every selected layer
- Feature Survival missing=0 PASS
- Forbidden Face Detail=0.00% PASS
- canonical hard gate PASS
- SA7.43 Golden LAB: 25.286020
- SA7.44 Golden LAB: 25.275946
- Browser fallback v12: 16.242237
- visual adoption HOLD

Verification:
- focused: 22/22 PASS
- ZeroBase: 650/650 PASS
- compileall: PASS
- git diff --check: PASS
- actual four-way reviewed
- SA7.43 -> SA7.44 delta reviewed

Drive:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_44_20261006_HOLD`

Folder ID:
`1leDBjSuG3hSkKbgHJPRPn0lHJpTUK-C7`

## SA7.45 Semantic Retention Observer — COMPLETE

### Goal

Add a model-agnostic, observer-only semantic-retention diagnostic inspired by CLIPasso / CLIPascene.

The observer answers:

> Did the candidate preserve the semantic identity/meaning of the source after abstraction?

This stage must not modify geometry, palette, layer selection, or rendering.

### Existing infrastructure to reuse

Minimalizer already has:
- `SemanticObservation`
- `DinoV3Observer` with injected optional extractor
- DINO spatial comparison
- Golden Gap diagnostic dimensions
- observer evidence that cannot override hard failures

SA7.45 should unify these into an inspectable semantic-retention report rather than adding a hard CLIP runtime dependency.

### Core contract

1. Observer input:
   - source observation
   - candidate observation
   - optional role/region observations
   - observer name / provenance

2. Output:
   - global semantic similarity
   - patch/local semantic similarity when aligned
   - optional per-role retention
   - semantic-retention score
   - availability state
   - observer provenance
   - explicit non-authoritative flag

3. Hard boundaries:
   - observer cannot alter production scene
   - unavailable observer cannot change production output
   - high observer score cannot rescue Feature Survival / face / anatomy / topology failure
   - low observer score may create diagnostic HOLD evidence only
   - no Golden raster/coordinates as observer input
   - no new mandatory transformers/CLIP dependency in production

4. CLIPasso / CLIPascene assimilation:
   - semantic preservation becomes an explicit diagnostic objective
   - fidelity vs simplicity can be reported, not directly optimized in production
   - role-local semantic loss can reveal when aggressive simplification destroys identity

### Preferred implementation order

1. Add a generic `SemanticRetentionReport`.
2. Compare frozen `SemanticObservation` pairs.
3. Support global + aligned patch/local retention.
4. Support optional role-local reports.
5. Add status:
   - AVAILABLE
   - UNAVAILABLE
   - DEGRADED
6. Bind report into evaluation/debug provenance only.
7. Prove hard failures cannot be overridden.
8. Run synthetic tests.
9. Reuse the existing locally cached DINOv3 runtime for GC001 if available.
10. Compare SA7.43 vs SA7.44 semantic-retention evidence without changing either image.
11. Preserve report artifacts.
12. Decide whether the observer contract is ready for PB3/SA3 and SA9 reuse.

## SA7.46 / SA7.47 after this

- SA7.46 Primitive-Type Advisor Research: StarVector
- SA7.47 Layer / Occlusion Evidence Research: LayerPeeler / SuperSVG
- SA7 closeout
- Post-SA7 Backport PB2 -> PB7
- SA8 -> SA9 -> SA10

## Current state declaration

SA7.45 is complete. The canonical continuation point is:

**SA7.46 Primitive-Type Advisor Research**

Current handoff: `docs/handoffs/HND-20261006-sa746-primitive-type-advisor-next.md`.
