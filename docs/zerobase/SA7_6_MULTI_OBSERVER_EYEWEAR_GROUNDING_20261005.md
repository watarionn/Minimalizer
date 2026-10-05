# SA7.6 Multi-Observer Eyewear Grounding — 2026-10-05

Status: FUSION FOUNDATION PASS / GC001 HOLD / PRODUCTION-NEUTRAL

## Goal

Combine independent observer evidence for eyewear without allowing any observer to become semantic authority.

## Implementation

Added `semantic_abstraction/eyewear_fusion.py`.

Evidence roles are explicit:

- structural: SA7.5 paired contour structure,
- region: SAM/Grounded-SAM-style bounded region hypothesis,
- feature_local: DINO-style local feature evidence.

The fusion layer does not run heavyweight models itself and does not render geometry.

## Hard rules

Promotion requires:

1. existing head|hair authority,
2. at least two independent evidence roles,
3. spatial agreement, not confidence alone,
4. source-supported masks clipped to authority,
5. confidence gate after spatial agreement,
6. face-feature-risk rejection,
7. deterministic order-invariant output.

Multiple high-confidence records from the same observer role cannot create a promotion by themselves.

The fusion result is still a candidate hypothesis. Semantic authority remains downstream and fail-closed.

## Verification

Focused SA7.5 + SA7.6: 11 PASS.
Full ZeroBase: 530 PASS.
git diff --check: PASS.

Tests cover:

- structural + region agreement promotion,
- same-role confidence stacking rejection,
- spatial disagreement rejection,
- deep-face eye-like evidence rejection,
- outside-authority evidence rejection,
- observer order invariance.

## GC001 runtime boundary

SA7.5 remains:

- paired: false
- confidence: 0.259110
- frame evidence only
- no certified left/right lens pair

The existing shared observer environment at `C:\Work\SharedAI\minimalizer-observers` was found and reused for normal ZeroBase execution. A direct heavyweight Torch/Transformers runtime probe did not complete normally during this stage. No duplicate heavyweight environment was installed and no model was re-downloaded.

Because no fresh independent region/feature-local GC001 evidence was available, SA7.6 correctly leaves GC001 at HOLD. Missing evidence is not replaced by handcrafted labels, Golden-derived geometry, or relaxed thresholds.

## Renderer decision

No renderer integration.
No visual adoption.
No four-way required because production rendering is unchanged.

## Next: SA7.7 Frozen Observer Artifact Reuse Bridge

1. locate/reuse canonical frozen Grounded-SAM observer artifacts rather than reinstalling models,
2. convert untouched bounded observer records into `EyewearObserverEvidence(role="region")`,
3. bind feature-local evidence only when an existing frozen DINO artifact/runtime is available,
4. preserve provenance and source coordinates,
5. feed the evidence into SA7.6 without changing its gates,
6. run GC001 and non-GC001 holdout,
7. only if the hypothesis becomes credible, expose it to SA7.4 grammar,
8. then run all visual hard gates and actual four-way.

Do not tune against GC001 until it passes. Do not create a second heavyweight observer environment merely to force this stage forward.
