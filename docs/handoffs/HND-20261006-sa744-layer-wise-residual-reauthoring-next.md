# HND-20261006 Minimalizer SA7.44 Layer-wise Residual Re-authoring Handoff

Date: 2026-10-06
Status: SA7.44 COMPLETE / SUPERSEDED BY SA7.45 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-sa745-semantic-retention-observer-next.md`.

SA7.43 implementation:
- PR #178
- merge SHA: `217c9c366661735a3d01d1352e5bb23ab0dbaacb`

Canonical SA7.43 record:
`docs/zerobase/SA7_43_ADAPTIVE_PRIMITIVE_BUDGET_20261006.md`

Cross-phase precedent plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Latest adopted visual baseline remains:
- `a60aaa12ff22c2f6384a598442964710ce939d87`
- Silhouette Proportion Recomposition

SA7.43 implementation is merged, but its GC001 visual candidate remains HOLD because Browser fallback v12 still wins the overall visual regression-floor review.

## SA7.43 closure

SA7.43 replaced the canonical macro path's fixed role capacities with one deterministic source-supported global allocator.

Before:
- hair capacity: 3
- major_clothing capacity: 2
- fixed role split

After:
- global macro cap: 5
- required minima: hair=1, major_clothing=1
- per-role hard maximum: 3
- extra slots compete globally using source-supported major-component area
- unused budget is allowed to remain unused

GC001 allocation:
- hair: 1
- major_clothing: 3
- unused: 1

GC001 evaluation:
- Feature Survival missing=0 — PASS
- Forbidden Face Detail=0.00% — PASS
- overall canonical hard gate — PASS
- face-guard writes outside face mask: 0
- Golden raster used in production: false
- SA7.42 Golden LAB: 25.2943
- SA7.43 Golden LAB: 25.2860
- Browser fallback v12 Golden LAB: 16.2422
- pixel delta vs SA7.42: 0.232699%

The SA7.42 -> SA7.43 visual difference is localized to a source-supported clothing mass rather than a broad restyling.

Verification:
- focused SA7.43/macro tests: 17/17 PASS
- ZeroBase: 641/641 PASS
- Python compileall: PASS
- git diff --check: PASS
- actual four-way reviewed

Drive:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_43_20261006_HOLD`

Folder ID:
`1amzsvY0wU47BlsDHK5ivQGjqSwL_YTsS`

## SA7.44 Layer-wise Residual Re-authoring — COMPLETE

### Goal

Start from the accepted coarse semantic masses and add only bounded, source-supported residual layers whose marginal representational value justifies their geometric cost.

Primary precedents:
- LIVE
- SuperSVG
- Primitive
- Geometrize

SA7.44 must not become "raise the primitive cap until pixels match." The intended model is coarse-first residual construction.

### Conceptual pipeline

Authorized source semantic mask
-> accepted coarse semantic geometry
-> rasterize current role geometry
-> compute source-supported residual inside that same semantic authority
-> split residual into connected candidate layers
-> reject tiny/unsafe/low-value residuals
-> rank bounded candidates by marginal source-support gain per complexity cost
-> add only accepted residual layers
-> fresh hard gates

### Production boundaries

- Coarse semantic geometry remains the base authority.
- Residual candidates may only use source pixels/masks already authorized for their role.
- No residual may cross into another semantic role merely to reduce raster error.
- Residual budget must be separate from base required minima.
- Residual layer count must have a strict hard global cap.
- Tiny fragments must not consume residual budget.
- Residual candidate order and selection must be deterministic.
- Golden/v12 are evaluation-only.
- CLIP/VLM/model scores remain research observers only.
- No generative redraw.

### Candidate value contract

Initial deterministic source-only dimensions should include:
1. source-supported residual area
2. residual area ratio within the semantic role
3. incremental source coverage gained
4. geometry complexity cost / vertex count
5. expansion / spill risk
6. deterministic role/component identity

Candidate acceptance should prefer high marginal support at low geometric cost.

A residual layer that does not materially improve source-supported coverage should not be emitted simply because budget remains.

### Hard safety gates

SA7.44 must preserve:
- Feature Survival missing=0
- Forbidden Face Detail=0.00%
- face raster safety
- anatomy/topology authority
- source coverage floors
- expansion limits
- role/subject spill protection
- deterministic production behavior
- no Golden production authority

### Preferred implementation order

1. Define a residual candidate/report schema.
2. Add a deterministic raster comparison between each authorized source role mask and its currently rendered coarse role geometry.
3. Extract connected residual components inside the source role authority.
4. Add minimum residual area/support thresholds.
5. Fit bounded coarse polygons to residual candidates under existing coverage/expansion guards.
6. Define a separate residual global cap and marginal-value ranking.
7. Integrate behind the current SA7.43 coarse macro path.
8. Add synthetic tests:
   - no residual -> no extra layer
   - one large missing source lobe -> one residual layer
   - tiny fragments rejected
   - higher-value residual wins under cap
   - residual cannot cross semantic authority
   - total residual cap enforced
   - deterministic input/repeat behavior
9. Run focused + full ZeroBase.
10. Generate GC001 candidate.
11. Run fresh SA7.35 hard gate.
12. Generate actual four-way and SA7.43 -> SA7.44 delta board.
13. Compare against Browser fallback v12.
14. Preserve evidence in Drive before any adoption decision.

## Post-SA7 execution order

After SA7.44-SA7.47 and SA7 closeout are complete, do not jump directly to SA8.

Run the adopted Post-SA7 Precedent Backport Pass:
- PB2: SA2 Evidence Adapter
- PB3: SA3 Importance / Policy
- PB4: SA4 Semantic Debug Board
- PB5: SA5 Face compatibility audit
- PB6: SA6 Anatomy / Occlusion evidence
- PB7: SA7 integration review
- then SA8 -> SA9 -> SA10

Canonical plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

Each backport stage must end as IMPLEMENTED, OBSERVER-ONLY, or NO-OP-BY-DESIGN and preserve all existing hard gates.

## Deferred next stages

Current research queue after SA7.44:
- SA7.45 Semantic Retention Observer: CLIPasso / CLIPascene
- SA7.46 Primitive-Type Advisor Research: StarVector
- SA7.47 Layer / Occlusion Evidence Research: LayerPeeler / SuperSVG

These are planning anchors only. SA7.44 evidence may refine the order.

## Current state declaration

SA7.44 is complete. The canonical continuation point is:

**SA7.45 Semantic Retention Observer**

Current handoff: `docs/handoffs/HND-20261006-sa745-semantic-retention-observer-next.md`.
