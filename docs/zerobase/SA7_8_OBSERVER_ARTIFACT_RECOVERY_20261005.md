# SA7.8 Observer Artifact Recovery / Reproduction Gate — 2026-10-05

Status: RECOVERY AUDIT PASS / HISTORICAL ZIP LOST-UNRESOLVED / MODEL CACHE RECOVERED

## Historical artifact recovery

Searched:

- GitHub repository and handoffs by exact ZIP name and SHA-256,
- Google Drive by exact filename, suite id, and observer-run terms,
- canonical Minimalizer Drive hierarchy,
- local Google Drive mount,
- local C:\Work tree.

The recorded artifact `GBLIND_HOLOMEN_20261005_frozen_observer_run.zip` was not found.

Expected SHA-256:
`de498aa0769c7aa48665d93dc4b603d69123247d69e3a48fa514ad942ea14892`.

Decision: historical ZIP is LOST/UNRESOLVED. The GitHub machine-readable summary remains valid historical run evidence, but cannot be promoted into spatial evidence.

## Runtime recovery

No duplicate environment or model download was required.

Existing shared runtime:
`C:\Work\SharedAI\minimalizer-observers\Scripts\python.exe`

Verified:

- Python 3.11.9
- torch 2.11.0+cu128
- CUDA available: true
- transformers 5.17.0

Existing Hugging Face cache contains:

- `IDEA-Research/grounding-dino-tiny`
- `facebook/sam-vit-base`
- `facebook/dinov3-convnext-tiny-pretrain-lvd1689m`

Therefore reproduction, if needed, must use this shared runtime and local cache only. Re-download/reinstall is not authorized merely to force progress.

## Frozen-contract constraint

The existing frozen Grounded-SAM production observer uses the Phase-E labels:

`hair, face-skin, limb, accessory`

and frozen prompt/thresholds. It does not contain an eyewear-specific label. Changing that frozen prompt to add glasses/goggles would be a new observer contract, not recovery of the historical run.

Accordingly:

- historical blind evidence may not be reinterpreted as eyewear,
- aggregate accessory evidence may not be converted into an eyewear mask,
- a new eyewear observer must be introduced and validated as a new observer version,
- non-GC001 validation must precede GC001 evaluation.

## Next: SA7.9 Eyewear Observer v1

Build a new, explicitly versioned observer using the already-cached Grounding-DINO + SAM runtime.

Requirements:

1. fixed generic eyewear prompt, frozen before GC001,
2. labels include glasses/goggles/sunglasses/eyewear without GC001-specific wording,
3. source-coordinate mask and provenance emitted through SA7.7,
4. test on synthetic/non-GC001 eyewear and no-eyewear fixtures first,
5. freeze thresholds before GC001,
6. run GC001 untouched,
7. fuse with SA7.5 through SA7.6,
8. renderer stays disconnected unless the fused evidence passes visual review.

No Golden input. No GC001 tuning.
