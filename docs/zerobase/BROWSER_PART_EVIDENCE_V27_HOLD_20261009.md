# BrowserFallback v27: browser-native part evidence / anime calibration HOLD

Date: 2026-10-09
Status: **RESEARCH OBSERVER COMPLETE / SEMANTIC VISUAL FAIL / PRODUCTION HOLD**
PR: https://github.com/watarionn/Minimalizer/pull/296 (Draft, unmerged)
Branch: research/browser-part-evidence-v27-20261009
Parent: held v26 PR #293. Main Public Facet v15 and Local Worker unchanged.

## Scope

After v26 identified source-observed boundaries missing in Facet, v27 tests
two independently verified non-generative browser observation channels for
semantic part hints, without giving any model final rendering authority.

1. MediaPipe Selfie Multiclass, ONNX conversion from
   senty-au/selfie_multiclass_256x256-ONNX at immutable revision
   6db8421a7150ac20558f2c24675078eb3a1a04d0.
   Downloaded actual checkpoint size 16,454,560 bytes; SHA-256
   35ec1ecd9ee7f85073c99c00020b7f6751b69506eeacf683bc8665f6117f85b0.
   Input is RGB float32 [1,256,256,3], stretched NHWC, scaled [0,1].
   Output logits [1,256,256,6], softmax applied explicitly.
   Categories: background, hair, body_skin, face_skin, clothes, accessories.
   Model and conversion licensed Apache-2.0; model weights from Google.
2. MediaPipe Pose Landmarker Lite (Google): pinned float16 task from official
   Google model storage; 5,777,746 bytes, SHA-256
   59929e1d1ee95287735ddd833b19cf4ac46d29bc7afddbbf6753c459690d574a.
   JavaScript package pinned at @mediapipe/tasks-vision 0.10.32; optional
   CPU execution through browser, no Local Worker, and no remote image inference.
3. Existing browser-U2NetP (foreground ONLY) and v26 lost-source-edge
   evidence form independent containment and edge constraints.

Both model bytes are hashed in the browser before being used. SHA mismatch,
download, browser-runner, segmentation, pose failure, missing U2NetP or malformed
upstream evidence **abstains**. No package or model binary added to normal
Minimalizer deployment. Explicit research source URLs are external CDN/HF
model downloads only; image content remains on the browser.

## Implementation

- web/static/browser-part-evidence-v27.js: separate ES module reusing
  existing bundled onnxruntime wasm, optional pinned pose JS, model checksum
  validation, source-backed masks and cross-evidence candidates.
- Model clothing evidence requires strong class probability >=0.72,
  margin >=0.32 and browser subject probability >=0.8, confidence >=0.25.
  Pose corridor additionally needs visible shoulder/elbow/wrist track
  (minimum visibility and presence 0.75) AND clothing/skin model confidence.
- Candidate role observations are explicitly non-authoritative: no part
  receives a semantic ownership claim or final color/silhouette rendering.
  Every v26 source-edge record remains semanticPart=unbound,
  bindingConfidence=0. Provenance records calibration=false and
  visibleOutputAuthority=false. Reject untrusted model SHA/provider IDs.
- web/static/index.html loads the *inactive* opt-in module on this research
  branch. app.js, browser-fallback.js and accepted profile paths unchanged.
- Tools: tools/run_browser_part_v27_chrome.py (actual Chrome, own UI request,
  source/frozen Facet equality, diagnostics), tools/analyze_browser_part_v27.py
  (independent external stage and preview auditor).
- Tests: tests/test_browser_part_evidence_v27.py, existing v25 workflow
  expanded; no new workflow. Synthetic cue, invalid provenance and SHA,
  abstention and deterministic contracts.

## Real Chrome 154, 340 x 340 original inputs

| Case | v26 lost-edge segments | Raw clothes cue segments | Left/right arm cues | Pose Lite | Semantic bound |
|---|---:|---:|---:|---|---:|
| Kyoko | 60 | 0 | 0/0 | not found | 0 |
| Noel | 74 | 10 | 0/0 | not found | 0 |
| Ririka | 83 | 32 | 0/0 | not found | 0 |

The six-class model did execute with matching SHA and returned source-clipped
class observations. However **independent visual review FAILS**:
- Kyoko: large source foreground wrongly modeled as background, no useful
  garment observations at strict confidence/margin thresholds.
- Noel: large part of silver hair falsely marked as clothes.
- Ririka: hair and facial-adjacent areas falsely marked as clothes.
- Pose Lite could not return one sufficiently confident landmark set
  for any of the 3 anime subjects.
- A strong class posterior is not proof that it is a true sleeve/garment.
  Do not lower thresholds to claim semantic improvement.

All 42 raw candidate groups remain **UNBOUND**. Newly accepted confident
arm or garment ownership is **0**; public visible Minimalizer changes **0**.
Existing frozen Facet images were verified byte-identical (3/3), so silhouette,
characteristic tie/sleeve colors and all old features remain untouched.
The color-coded diagnostic preview does not draw any facial detail or other
content into final Minimalizer.

## Verifications

- 5 new v27 synthetic tests + all inherited browser mode tests:
  **54 pytest PASS**, JS syntax, Python compile, GitHub Actions PASS on
  code-bearing commit 02645f47ce9ae5ff2857e84e5802e74dc8aa3da2.
- Real independent Chrome 154 replay with model inference repeated:
  **18/18 source/Facet/category-map/diagnostic-preview/metrics/stage files
  byte-identical by SHA-256** across three inputs.
- Independent source/frozen output equality, class palette limits,
  stage SHA, unbound/zero-authority and diagnostic overlay boundaries verified.
- The renderer and app routing were not modified. No production tests/deploy
  needed because this is a held research-only PR.

## Gate and next

**v27 browser inference connector + evidence provenance DONE;
semantic transferability to anime FAIL / HOLD.**

Next v28 must evaluate an **anime-domain** parser / pose observer that can
actually distinguish hair from clothing and reconstruct supported arm
localization, under browser-only resource constraints. Prior research
SA10.27 AnimeSeg Mask2Former (12-class, Python isolated) is valuable
reference but NOT automatically portable or running in the browser. Compare
model size, license, WebAssembly/ONNX support, non-local browser memory,
and SHA-pinned original sources before selecting one. A model is still
observation-only until cross-part error review passes. Unknown/unbound
is a valid result, no invented face internals, no generative fill.
Retain v25/v26/v27 baselines and this case-corpus diagnostic gallery.

## Evidence

Canonical Drive: chatGPT及びCodex用/Minimalizer/PartEvidenceV27_20261009
https://drive.google.com/drive/folders/1M24c2x1pNl5N1jxzh_W_75fV4c9o5v3k

Required evidence: v27_source_facet_classes_cues.png,
v27_metrics.json/csv, v27_report.md, v27_stages_metrics.zip,
v27_replay_sha_verify.json, SHA read-after-write evidence manifest,
research code/test/Chrome/audit scripts.

Do not merge PR #296 or promote the photographic model as a trusted anime
arm/garment interpreter.
