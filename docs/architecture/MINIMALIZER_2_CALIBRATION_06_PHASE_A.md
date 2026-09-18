# Minimalizer 2.0 Calibration 06 Phase A

Updated: 2026-09-17
Status: PASS locally
Scope: non-generative AI analysis-guidance foundation

## Policy boundary

Minimalizer 2.0 no longer treats all AI/ML as prohibited.
The project rule is now **no generative AI for output-image creation or completion**.

Allowed uses include input-image analysis, detection, foreground segmentation,
semantic segmentation, and guide masks. Stable Diffusion, image-to-image,
generative fill, AI paint-in, and AI missing-region completion remain prohibited.

The final image is still produced only by Minimalizer's own decomposition path:
`pixel -> micro structure -> superpixel/region -> merged region -> primitive`.

rembg and MediaPipe are approved candidate analysis providers. Their masks are
hints only and must never become final rendered geometry directly.

## Existing V2 integration points

The V2 architecture already had the required semantic plumbing before this phase:

- `ImageBundle.subject_prob` / `subject_confidence`
- `RegionAnnotation.semantic_tag` / `semantic_confidence`
- Region Merge subject/background hard barriers
- configurable semantic hard-pair barriers
- semantic propagation through the Region Merge tree
- semantic-aware contour, palette, detail-budget, and primitive stages

Therefore rembg / MediaPipe do not replace Region Merge or Primitive generation.
They feed information into the existing architecture immediately before initial RAG construction.

## Phase A implementation

Added `minimalize_engine/v2/analysis_guidance.py` with:

- `AnalysisGuidance` for subject probability/confidence maps
- `SemanticGuide` for per-class semantic confidence masks
- strict shape/dtype/range/provider/model validation
- analysis-resolution confidence-map resizing
- conservative superpixel-level semantic aggregation

`minimalize_v2(..., guidance=...)` now passes subject maps into `ImageBundle` and
converts semantic confidence maps into the existing `RegionAnnotation` contract.
No guide means the old path is preserved exactly.

The aggregation rule averages each class confidence across every initial superpixel
and assigns the strongest class plus its mean confidence. Mixed-boundary superpixels
therefore lose confidence naturally instead of being treated as hard semantic truth.
The existing Region Merge threshold remains responsible for deciding whether a
semantic distinction is strong enough to protect.

No visual threshold, SLIC target, Region Merge cost, hierarchy cut, contour rule,
facet gate, palette rule, primitive rule, or preset behavior was changed.

## Dependency reconnaissance

No new runtime dependency was installed in Phase A.

RDC default Python is `3.14.5`; Python `3.11` is also installed.
`rembg[cpu]==2.0.84` resolves successfully under the current 3.14 environment in
pip dry-run, despite upstream documentation/metadata currently being inconsistent
about the 3.14 support boundary.

`mediapipe==1.0.1` resolves under Python 3.14 but selects
`opencv-contrib-python 5.0.0.93`, which conflicts with Minimalizer's `opencv<5` policy.
Python 3.11 plus an explicit `opencv-contrib-python<5` constraint resolves MediaPipe
with `opencv-contrib-python 4.14.0.94` in pip dry-run. The preferred evaluation setup
is therefore an isolated Python 3.11 environment rather than modifying the current
Minimalizer runtime environment.

## Provider plan

Phase B should evaluate rembg first because foreground/background separation directly
addresses background leakage while adding only one guidance channel to V2.

Initial local model shortlist:

1. `isnet-anime` for character/anime illustration foreground masks
2. `isnet-general-use` for mixed illustration/photo inputs
3. `u2net_human_seg` for human-focused comparison
4. `birefnet-general-lite` only if the first three leave a clear quality gap

MediaPipe follows after the foreground contract is measured. Its Image Segmenter can
supply per-class confidence masks, which map directly to `SemanticGuide` without
turning semantic masks into final geometry.

Grounded-SAM and YOLO segmentation remain deferred. They are not dependencies of
Calibration 06 unless rembg + MediaPipe leave a demonstrated unresolved need.

## Validation

Focused guidance/RAG/known-issue/pipeline suite:
`23 passed`.

V2-focused repository regression:
`178 passed, 334 deselected, 1 warning`.

The new empty-guidance regression proves that the algorithm digest is identical to
the no-guidance path. Phase A is therefore an additive analysis contract only.

## Next boundary

Proceed to Calibration 06 Phase B: isolated rembg foreground-mask adapter and approved
18-case model comparison. Do not add MediaPipe to the main requirements yet.
Do not create/update a PR, touch `main`, merge, deploy, or run GitHub Actions.
