# ZeroBase 2nd Cycle Phase 4 — Semantic Part Decomposition

Status: **CLOSED / PASS**

## Objective

Phase 4 consumes the Phase 3 canonical subject mask and decomposes the subject into semantic parts before any region binding or geometrization.

The fixed Phase 4 part vocabulary is:

- head
- hair
- face
- neck
- torso
- left_arm
- right_arm
- lower_body
- major_clothing
- accessory_or_held_object
- unknown

Unknown is an allowed outcome. Phase 4 must not force unsupported pixels into a confident semantic label.

## Evidence architecture

Phase 4 uses existing non-generative analysis assets rather than inventing a new all-purpose parser.

- **RTMLib WholeBody** supplies BODY17 structure and retains the full 133-point output.
- WholeBody face points 23–90 (68 facial landmarks) are the primary face geometry evidence when their confidence is sufficient.
- The deterministic **structure face locator** remains an independent source-color fallback and diagnostic score.
- Source-image color prototypes grow hair from the structural head region.
- **MediaPipe selfie_multiclass_256x256** is used only as an optional hair-growth guard when it supplies meaningful hair evidence.
- Deterministic shape/color rules detect major accessories:
  - vivid central accent for items such as Kyoko's green tie
  - peripheral thin linear evidence for items such as Raden's rod

No analyzer has final rendering authority. No generated image content, inpainting, img2img, Generative Fill, or missing-part synthesis is used.

## Face alignment correction

The first Phase 4 closure used only the source-color face locator for the final visible face mask. Diagnostic review showed that Raden's face was too small and shifted left.

Measured before correction:

- Raden source-color face bbox: `[124, 99, 61, 58]`
- WholeBody face68 visible point span: approximately `x=135..206, y=91..155`
- WholeBody face68 mean confidence: approximately `0.945`

The correction preserves RTMLib's full 133-point output instead of discarding everything after BODY17. When at least 24 face landmarks are visible at confidence >= 0.30 and their mean confidence is >= 0.55, Phase 4 forms a convex-hull face mask from those landmarks with a small deterministic dilation. The source-color face locator remains the fallback when reliable face68 evidence is unavailable.

This is a general evidence-path correction, not a Raden-specific coordinate adjustment.

## Why MediaPipe is optional only

The earlier Calibration 06 Phase D result remains valid: MediaPipe multiclass is not semantic ground truth for anime/VTuber images.

On Diagnostic-2:

- Kyoko MediaPipe hair evidence was effectively absent, so the hair result remains source-color driven.
- Raden MediaPipe hair evidence was meaningful and cleanly separated long hair from the dark sleeves. It is therefore used only to constrain deep hair growth.

Canonical semantic model:

- model: `selfie_multiclass_256x256`
- MediaPipe: `1.0.1`
- model SHA-256: `c6748b1253a99067ef71f7e26ca71096cd449baefa8f101900ea23016507e0e0`

## Diagnostic-2 results

### Hyakuto Kyoko

- Source SHA-256: `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`
- RTMLib structural quality: `0.7377348120641755`
- Face source: `rtmlib-wholebody-face68`
- Face bbox: `[128, 109, 86, 73]`
- Face landmark confidence: `0.8971750140190125`
- Source-color face score: `4.302988773664984`
- Accessory: `vivid-accent`
- Accessory score: `0.8063757451968034`
- Unknown ratio: `0.03687786960514233`
- Visual QA: **PASS**

The diagnostic view separates the orange hair, face, neck, torso, both arms, lower-body support, clothing masses, and the bright green tie/accent. The face68 hull remains visually aligned with the source face.

Part coverage:

- hair: `0.26912764003673095`
- face: `0.08830119375573921`
- torso: `0.10701561065197429`
- left_arm: `0.0498989898989899`
- right_arm: `0.10877869605142332`
- lower_body: `0.23072543617998165`
- major_clothing: `0.06863177226813591`
- accessory_or_held_object: `0.003985307621671258`

### Juufuutei Raden

- Source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- RTMLib structural quality: `0.7565533480229997`
- Face source: `rtmlib-wholebody-face68`
- Face bbox: `[132, 88, 78, 71]`
- Face landmark confidence: `0.9452449679374695`
- Source-color face score: `4.3900166495983495`
- Accessory: `held-linear`
- Accessory score: `0.6765070756343059`
- Unknown ratio: `0.006407118380510841`
- Visual QA: **PASS**

The initial source-color hair growth incorrectly consumed large portions of the dark sleeves, and the initial source-color-only face mask was visibly too small and left-shifted. Both failures were repaired inside Phase 4 rather than hidden downstream. The final diagnostic view separates long hair, a correctly aligned face, torso, both large sleeves/arms, lower support, clothing masses, and the held rod.

Part coverage:

- hair: `0.2802862326143923`
- face: `0.05834077230973018`
- torso: `0.2759092348892792`
- left_arm: `0.15001295821694935`
- right_arm: `0.1421084458778472`
- lower_body: `0.025873239842197714`
- major_clothing: `0.054294929017767155`
- accessory_or_held_object: `0.0048953264030869355`

## Mandatory stage artifacts

Runtime artifacts:

`artifacts/zerobase2/<case_id>/phase_04/`

Each case contains:

- `04_part_map.png`
- `04_part_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`
- `part_masks/<semantic-part>.png`

Persistent diagnostic snapshots:

`docs/zerobase/diagnostics/phase04/<case_id>/`

The stage record also persists BODY17 plus face68 keypoints/scores so the face evidence can be audited independently.

## Determinism

The same Diagnostic-2 inputs/config were executed twice. The mandatory visible artifacts were byte-identical by SHA-256.

Kyoko:

- part map: `da7153b8e6ef01ef7043248e93600fb1ef2bf60e6c1a3d5009754508e9646c6a`
- overlay: `1b4dadd30d6a12fad62414f0e3dde875466b2c188dfefdb7e52355ac2a7fa24d`

Raden:

- part map: `1676c7351d149c85bc4e9eacdb3d077ff1253b0a4a3a6472e7e83540e6b9884b`
- overlay: `c5984f061ee98572b2df97f51b307c3faa2bda27ee55323e50f35c5f0b68ee53`

## Regression

- Phase 4 tests: **6 passed**
- RTMLib guidance tests: **9 passed**
- Focused Phase 4 + RTMLib set: **15 passed**
- Full ZeroBase suite: **77 passed**
- Local merge stable regression/Web set: **131 passed**
- Phase 16 corpus local gate: **PASS**
- Real-server local smoke: **PASS**
- `LOCAL_MERGE_VALIDATION_PASS`
- `git diff --check`: **PASS**

## Gate decision

Phase 4 remains **CLOSED / PASS** for Diagnostic-2.

The Phase 3 silhouette is now represented as semantic parts sufficiently well to proceed. The Raden hair/sleeve failure and the face size/alignment failure were both detected and repaired inside Phase 4 before Phase 5.

The next phase is **Phase 5: Structural Layout Graph**.

Phase 5 must consume these corrected part masks and establish explicit attachment, spatial, containment, and front/behind relationships. It may not reinterpret a broken Phase 4 part map to conceal semantic decomposition errors.
