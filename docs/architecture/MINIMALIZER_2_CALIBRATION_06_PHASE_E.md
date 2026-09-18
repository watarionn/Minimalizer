# Minimalizer 2.0 Calibration 06 Phase E

Updated: 2026-09-18
Status: PASS as optional high-quality semantic guidance
Scope: limited Grounded-SAM semantic-part evaluation

## Goal

Evaluate Grounded-SAM only for the semantic gaps demonstrated by Calibration 06 Phase D.
The target gaps are hair, face/skin, body-part, and accessories.

The accepted foreground contract remains fixed:
`rembg isnet-anime + confidence_power=2.0`.

MediaPipe remains an optional lightweight semantic hint provider.
Grounded-SAM must supplement it, not replace rembg, Region Merge, Primitive fitting, or final Minimalizer rendering.
Grounded-SAM masks are analysis evidence only and are never rendered directly as final geometry.

## Isolated environment

Grounded-SAM stayed outside the base Minimalizer requirements:

- Python `3.11.9`
- PyTorch `2.11.0+cu128`
- torchvision `0.26.0+cu128`
- Transformers `5.17.0`
- CUDA `12.8`
- GPU: NVIDIA GeForce RTX 5060
- isolated environment size: approximately `4.47 GB`
- base requirements modified: no

The evaluated model pair is:

- detector: `IDEA-Research/grounding-dino-tiny`
- segmenter: `facebook/sam-vit-base`

Official GroundingDINO, Segment Anything, and Grounded-Segment-Anything repositories were verified as Apache-2.0 licensed.

The runtime adapter is lazy-loaded. Importing the normal Minimalizer package does not require Torch or Transformers unless Grounded-SAM is explicitly requested.

## Prompt scope

The evaluation intentionally limits prompts to unresolved character-part semantics:

`hair / face / arm / hand / leg / ribbon / bow / hat / headband / necklace / earrings / microphone / accessory`

Canonical Minimalizer semantic channels are:

`hair / face-skin / limb / accessory`

This is not an open-ended semantic detector and is not intended to infer arbitrary scene semantics.

## Provider quality gates

Grounded-SAM evidence is accepted only behind the existing rembg foreground authority.

Current Phase E provider gates:

- rembg subject threshold: `0.50`
- Grounding DINO detection threshold: `0.20`
- text threshold: `0.20`
- hair maximum subject ratio: `0.50`
- face-skin maximum subject ratio: `0.15`
- limb maximum subject ratio: `0.45`
- accessory maximum subject ratio: `0.30`

An oversized part mask is discarded before it enters `SemanticGuide`.
This specifically prevents broad false-positive masks from acting as semantic authority.

The Approved-18 run rejected `6` oversized detections.
The Raora-Panthera probe was the motivating guard case: an initially oversized hair detection was reduced to a bounded semantic contribution without changing Region Merge thresholds.

## Approved-18 semantic result

Grounded-SAM completed all `18 / 18` Approved cases.

Non-zero semantic coverage:

- hair: `18 / 18`
- face-skin: `18 / 18`
- accessory: `18 / 18`
- limb: `17 / 18`
- only Houshou-Marine had zero accepted limb coverage

Mean active image-area ratios:

- hair: `0.1230`
- face-skin: `0.0290`
- limb: `0.0887`
- accessory: `0.1026`

Mean union of accepted semantic evidence: `0.3149`.
Mean overlap between semantic channels: `0.0281`.

Performance on the evaluation GPU:

- mean Grounded-SAM inference: approximately `0.307 s / image`
- peak CUDA memory: approximately `1378.6 MB`

This closes the largest Phase D coverage gap. MediaPipe provided hair and face-skin evidence in only `6 / 18` cases each; the bounded Grounded-SAM provider produced non-zero hair and face-skin evidence in `18 / 18`.

## V2 integration result

The integration comparison isolates Grounded-SAM's incremental effect.

Baseline:
`rembg isnet-anime + MediaPipe` from Phase D.

Guided:
the same baseline plus bounded Grounded-SAM semantic evidence.

Approved-18 result:

- digest changed: `17 / 18`
- hard invariant failures: `0 / 18`
- mean final Region Merge root delta: `0.0`
- mean visual-group delta: `+0.333`
- mean contour vertex delta: `-2.944`
- mean changed initial semantic regions: `277.444`
- mean semantic-region delta at confidence >= `0.50`: `+115.333`
- mean semantic-region delta at confidence >= `0.80`: `+63.611`
- semantic hard barriers: `0`

The important result is that semantic evidence increases substantially without changing the final Region Merge root count on average and without enabling semantic hard barriers.

Grounded-SAM therefore changes local downstream interpretation rather than globally fragmenting the region topology.

## Representative visual review

Representative `source / Phase D / Phase E` triplets were rendered for ten guard cases.

The changes remained local around face, hair, limb, and accessory structure rather than repainting the whole character.

Visual-group examples:

- Aki-Rosenthal: `36 -> 39`
- Hakos-Baelz: `43 -> 43`
- Houshou-Marine: `39 -> 37`
- Isaki-Riona: `36 -> 38`
- Kikirara-Vivi: `34 -> 36`
- Koganei-Niko: `38 -> 37`
- Koseki-Bijou: `35 -> 36`
- Raora-Panthera: `34 -> 34`
- Shiori-Novella: `36 -> 36`
- Vestia-Zeta: `40 -> 40`

No representative case showed runaway whole-subject fragmentation.
The small positive visual-group delta is accepted only because the added groups are localized semantic structure, not a new global merge policy.

## Phase E decision

Accept Grounded-SAM as an **optional higher-cost semantic gap filler**.

Accepted architecture:

`rembg`
-> foreground authority

`MediaPipe`
-> optional lightweight high-confidence semantic hint, especially clothes

`Grounded-SAM`
-> optional higher-quality hair / face-skin / limb / accessory evidence

`Minimalizer Region Merge / Primitive pipeline`
-> final geometry decision and rendering

Grounded-SAM is not:

- a default required dependency
- foreground authority
- semantic ground truth
- a source of semantic hard barriers
- a final geometry renderer
- a replacement for MediaPipe
- a reason to introduce YOLO segmentation yet

Provider fusion uses confidence-preserving maximum evidence for shared labels.
The rembg subject mask remains the outer authority for all semantic providers.

## Validation

Grounded-SAM adapter unit tests: `8 passed`.

Focused analysis-guidance regression:
`23 passed`.

V2-focused repository regression:
`195 passed, 334 deselected, 1 warning`.

The warning is the existing Starlette/httpx deprecation warning and is unrelated to Phase E.

Machine-readable evidence:
`MINIMALIZER_2_CALIBRATION_06_PHASE_E_EVALUATION.json`.

Reproduction tools:

- `tools/evaluate_groundedsam_semantics.py`
- `tools/compare_groundedsam_guided_v2.py`
- `tools/render_groundedsam_guided_visual.py`

## Next boundary

Phase E evidence is complete.

The next engineering step is to update `MINIMALIZER_2_CURRENT.md` and `MINIMALIZER_2_HANDOFF.md`, then create the local engineering/handoff commits.

Do not create or update a PR, touch `main`, merge, deploy, or intentionally run GitHub Actions without explicit approval.
