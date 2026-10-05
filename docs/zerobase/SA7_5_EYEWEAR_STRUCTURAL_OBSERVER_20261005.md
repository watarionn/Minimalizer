# SA7.5 Eyewear Structural Observer — 2026-10-05

Status: FOUNDATION PASS / FAIL-CLOSED ON GC001 / PRODUCTION-NEUTRAL

## Goal

Replace generic eyewear color fragments with explicit structural evidence before geometry is authorized.

## Implementation

Added `semantic_abstraction/eyewear_structure.py`.

`EyewearStructuralEvidence` separates:

- left lens hypothesis,
- right lens hypothesis,
- frame evidence,
- bridge evidence,
- paired/unpaired state,
- confidence.

The observer is evidence only. It does not create SemanticPart authority and is not connected to the production renderer.

## Generic constraints

The observer:

- operates only inside source-supported `head | hair` authority near the upper face,
- excludes central facial-feature space from generic structural support,
- prefers closed contour structures over open hair strokes,
- requires paired candidates to straddle the face center,
- bounds paired candidates to the upper-face neighborhood,
- rejects remote/tall narrow closed hair loops,
- fails closed when a credible pair cannot be established.

It does not contain GC001 coordinates, colors, names, or Golden geometry.

## Synthetic verification

Five focused tests cover:

1. paired worn structure -> two lenses + frame + bridge,
2. authority containment,
3. eye-like marks inside the face do not become eyewear,
4. missing face fails closed,
5. deterministic repeatability.

Focused: 5 PASS.

## GC001 evidence review

GC001 was evaluated only after the generic synthetic tests.

Early iterations correctly exposed two failure modes:

- broad edge support absorbed hair strands,
- permissive closed-contour pairing could pair a real goggle-side contour with an unrelated hair/ornament contour.

Those were not accepted as success.

Final observer result on GC001:

- paired: false
- confidence: 0.25911
- lens hypotheses: none
- bridge: none
- frame evidence exists in the upper-face/head region

Interpretation: the available Phase4 coarse masks plus classical contour evidence are insufficient to certify the two-lens structure without risking false eyewear. The observer therefore fails closed.

This is the intended safety behavior. We do not tune GC001-specific thresholds until it says PASS.

## Renderer decision

No renderer integration.
No visual adoption.
No four-way required because production output is unchanged.

SA7.4 grammar remains ready to consume structured eyewear evidence once it is sufficiently grounded.

## Next: SA7.6 Multi-Observer Eyewear Grounding

Use already-available observer infrastructure as additional evidence, not authority:

- Grounded-SAM/SAM region hypothesis,
- DINO feature-local evidence/similarity,
- structural contour evidence from SA7.5.

Fuse evidence deterministically into a candidate hypothesis. Semantic promotion remains gated and fail-closed.

Required before renderer connection:

- non-GC001 synthetic/fixture coverage,
- source support,
- head|hair authority containment,
- no face-feature promotion,
- credible GC001 debug overlay,
- deterministic rerun,
- then SA7.4 grammar integration and unchanged visual hard gates.
