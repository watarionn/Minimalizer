# Minimalizer 2.0 Calibration 06 Phase D

Updated: 2026-09-18
Status: PASS as limited semantic guidance
Scope: MediaPipe multiclass semantic-hint evaluation

## Goal

Evaluate MediaPipe only as non-generative semantic analysis.
Its masks are hints for Minimalizer's existing region/primitive pipeline and are never output geometry.
The accepted Phase C foreground contract remains fixed:
`rembg isnet-anime + confidence_power=2.0`.

## Isolated environment

MediaPipe stayed outside the base Minimalizer requirements:
- Python `3.11.9`
- MediaPipe `1.0.1`
- opencv-contrib-python `4.14.0.94` (`<5` preserved)
- model: `selfie_multiclass_256x256`
- Approved-18: `18 / 18`

The runtime adapter is lazy-loaded, so importing Minimalizer does not import MediaPipe.
## Semantic model result

The model returns six confidence classes:
`background / hair / body-skin / face-skin / clothes / others`.

Approved-18 mean foreground coverage was only `0.2338`.
Mean class area was dominated by background `0.7662` and clothes `0.1977`.
Hair averaged `0.0088`; face-skin averaged `0.0025`.
Hair was non-zero in only `6 / 18` cases, and face-skin in only `6 / 18`.

Three severe low-foreground cases demonstrate the anime-domain gap:
- Hakos-Baelz: `0.0065`
- Raora-Panthera: `0.0099`
- Vestia-Zeta: `0.0172`

Therefore MediaPipe multiclass is not accepted as semantic ground truth for the Approved-18 character domain.
Its clothes evidence is useful, but hair/face/skin coverage is too sparse and input-dependent for authority.
## V2 integration result

The comparison baseline is Phase C rembg-only guidance.
MediaPipe foreground classes are multiplied by the rembg subject probability before entering `SemanticGuide`.
No semantic hard pairs are enabled.

Approved-18 rembg-only vs rembg + MediaPipe:
- digest changed: `15 / 18`
- hard invariant failures: `0 / 18`
- mean final Region Merge root delta: `0.0`
- mean visual-group delta: `-0.333`
- mean high-confidence semantic regions: `68.5`
- semantic hard barriers: `0`

This is a safe additive effect: the Region Merge topology is not globally fragmented, and the semantic layer does not introduce new hard barriers.
The semantic hints mainly influence downstream contour/primitive/palette/detail decisions where existing confidence gates already apply.
## Visual review

All 18 cases were rendered as `source / rembg-only / rembg+MediaPipe` triplets.

Useful or simplifying changes were visible in Gigi-Murin, Houshou-Marine, Koseki-Bijou, Momosuzu-Nene, and Todoroki-Hajime.
Small instability remained around face/hair/upper-body structure in Isaki-Riona, Koganei-Niko, and Shiori-Novella.
Hakos-Baelz, Raora-Panthera, and Vestia-Zeta showed effectively no semantic benefit because the model classified almost the whole character as background.

The visual review confirms the numeric result: MediaPipe can contribute weak high-confidence semantic evidence, especially for clothes, but cannot be the sole source of character-part semantics.

## Phase D decision

Accept MediaPipe as an **optional high-confidence semantic hint provider only**.
Do not treat its labels as semantic authority.
Do not enable `semantic_hard_pairs` from these masks.
Do not render MediaPipe masks directly.
Keep rembg as the foreground authority and use rembg probability to gate MediaPipe foreground confidence.
## Validation

Focused rembg/MediaPipe/analysis-guidance tests: `15 passed`.
V2-focused repository regression: `187 passed, 334 deselected, 1 warning`.
Machine-readable results: `MINIMALIZER_2_CALIBRATION_06_PHASE_D_EVALUATION.json`.
Reproduction tools:
- `tools/evaluate_mediapipe_semantics.py`
- `tools/compare_mediapipe_guided_v2.py`
- `tools/render_mediapipe_guided_visual.py`

## Next boundary

Proceed to Calibration 06 Phase E: **limited Grounded-SAM semantic-part evaluation**.
The reason is now demonstrated rather than speculative: Approved-18 still lacks reliable hair and face/skin semantics, and some images receive almost no MediaPipe foreground coverage.

Phase E must target only the unresolved semantic gaps, not replace rembg or Minimalizer's Region Merge/Primitive architecture.
Evaluate hair, face/skin, body-part, and accessory prompts first. Keep YOLO segmentation deferred.
Grounded-SAM masks remain guidance only and must never become final geometry.

Do not create/update a PR, touch `main`, merge, deploy, or intentionally run GitHub Actions without explicit approval.
