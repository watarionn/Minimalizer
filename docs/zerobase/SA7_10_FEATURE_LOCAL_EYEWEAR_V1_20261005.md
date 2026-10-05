# SA7.10 Feature-Local Eyewear Evidence v1 — 2026-10-05

Status: CONTRACT PASS / DINOv3 RUNTIME VERIFIED / GC001 HOLD

## Goal

Add an independent feature-local evidence role for SA7.6 without copying SA7.9 Grounded-SAM regions.

## Frozen contract

Version: `sa7.10-v1`
Similarity threshold: 0.72
Minimum connected component: 2 feature cells
Maximum authority ratio: 0.30

The observer:

- consumes frozen local embeddings,
- consumes a prototype supplied from a non-target reference,
- clips to independently supplied head|hair authority,
- emits only bounded feature_local evidence,
- carries no semantic label and grants no authority,
- rejects isolated and oversized components.

The contract was frozen before any GC001 feature-local evaluation.

## Verification

Synthetic + SA7.6 focused tests: 12 PASS before GC001 runtime inspection.

Covered:

- bounded coherent component,
- single-cell noise rejection,
- oversized component rejection,
- outside-authority rejection,
- deterministic output.

## Existing runtime

The already-cached model was loaded successfully offline:

`facebook/dinov3-convnext-tiny-pretrain-lvd1689m`

Runtime output includes spatial feature maps:
56x56, 28x28, 14x14, 7x7.

No model download or new environment was required.

## GC001 independence gate

SA7.10 intentionally does not run GC001 similarity yet.

A DINO prototype cannot be derived from:

- GC001 itself,
- SA7.9 GC001 boxes,
- Rinka Golden,
- post-hoc human marking of GC001.

Any of those would make the feature-local observer dependent on the region observer or target outcome.

No pre-frozen non-GC001 eyewear prototype bank currently exists.

Decision: GC001 HOLD. This is an independence requirement, not a runtime failure.

## Next: SA7.11 Non-Target Eyewear Prototype Bank

1. select non-GC001 eyewear references before target evaluation,
2. freeze source hashes and prototype extraction rule,
3. include negative/no-eyewear references,
4. extract DINOv3 features with the existing cached model,
5. build a small deterministic prototype bank,
6. validate on non-target holdout,
7. freeze bank hash,
8. only then run GC001 once,
9. feed feature-local evidence + SA7.9 region evidence into unchanged SA7.6 fusion.

Renderer remains disconnected.
