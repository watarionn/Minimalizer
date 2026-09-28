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

- **RTMLib WholeBody** supplies structural evidence and BODY17 keypoints.
- The existing deterministic **structure face locator** supplies source-color face evidence.
- Source-image color prototypes grow hair from the structural head region.
- **MediaPipe selfie_multiclass_256x256** is used only as an optional hair-growth guard when it supplies meaningful hair evidence.
- Deterministic shape/color rules detect major accessories:
  - vivid central accent for items such as Kyoko's green tie
  - peripheral thin linear evidence for items such as Raden's rod

No analyzer has final rendering authority. No generated image content, inpainting, img2img, Generative Fill, or missing-part synthesis is used.

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
- Face bbox: `[142, 105, 58, 61]`
- Face score: `4.302988773664984`
- Accessory: `vivid-accent`
- Accessory score: `0.7894138679493761`
- Unknown ratio: `0.03851239669421488`
- Visual QA: **PASS**

The diagnostic view separates the orange hair, face, neck, torso, both arms, lower-body support, clothing masses, and the bright green tie/accent.

Part coverage:

- hair: `0.3196510560146924`
- face: `0.03851239669421488`
- torso: `0.15399449035812673`
- left_arm: `0.0498989898989899`
- right_arm: `0.10877869605142332`
- lower_body: `0.23074380165289257`
- major_clothing: `0.042277318640955006`
- accessory_or_held_object: `0.003985307621671258`

### Juufuutei Raden

- Source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- RTMLib structural quality: `0.7565533480229997`
- Face bbox: `[124, 99, 61, 58]`
- Face score: `4.3900166495983495`
- Accessory: `held-linear`
- Accessory score: `0.7318319885380941`
- Unknown ratio: `0.016082587036023843`
- Visual QA: **PASS**

The initial source-color hair growth incorrectly consumed large portions of the dark sleeves. The optional MediaPipe hair guard fixed that failure at Phase 4 rather than hiding it downstream. The final diagnostic view separates long hair, face, torso, both large sleeves/arms, lower support, clothing masses, and the held rod.

Part coverage:

- hair: `0.2908255823998618`
- face: `0.03025023756731074`
- torso: `0.30061623520603564`
- left_arm: `0.15001295821694935`
- right_arm: `0.1442249546462407`
- lower_body: `0.025873239842197714`
- major_clothing: `0.03796757566158897`
- accessory_or_held_object: `0.0033115443314999855`

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

## Determinism

The same Diagnostic-2 inputs/config were executed twice. The mandatory visible artifacts were byte-identical by SHA-256.

Kyoko:

- part map: `73776934f33c1c9a54f08645167ad470812afca7c90b9ffb3133fb7e2baa1c87`
- overlay: `19424aea895e04a332c11443c92f49593c9f531db7346b18e9ca916f8d1a1e3d`

Raden:

- part map: `dda6e51e4f854f5f955ada8b7b19eadf40d02051c06f7fdef952ecf09013838d`
- overlay: `8ece94edb2b87d4ddf29a74dd76cf25893846048bc44569066974f3523036ff7`

## Regression

- New Phase 4 tests: **5 passed**
- Full ZeroBase suite: **76 passed**
- Local merge stable regression/Web set: **131 passed**
- Phase 16 corpus local gate: **PASS**
- Real-server local smoke: **PASS**
- `LOCAL_MERGE_VALIDATION_PASS`
- `git diff --check`: **PASS**

## Gate decision

Phase 4 is **CLOSED / PASS** for Diagnostic-2.

The Phase 3 silhouette is now represented as semantic parts sufficiently well to proceed. Crucially, the Raden hair/sleeve failure was detected and repaired inside Phase 4 before closure.

The next phase is **Phase 5: Structural Layout Graph**.

Phase 5 must consume these part masks and establish explicit attachment, spatial, containment, and front/behind relationships. It may not reinterpret a broken Phase 4 part map to conceal semantic decomposition errors.
