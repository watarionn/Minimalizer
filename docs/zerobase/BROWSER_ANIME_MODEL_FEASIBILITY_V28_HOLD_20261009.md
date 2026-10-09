# BrowserFallback v28: anime-domain model feasibility — Kyoko source-bound audit

Date: 2026-10-09
Status: **FEASIBILITY STUDY COMPLETE / ANIME PARSER BROWSER GATE HOLD**
PR: research/browser-anime-model-feasibility-v28-20261009 (stacked on held v27 #296)
Default Public Facet v15, app.js, browser-fallback.js and Local Worker: **UNCHANGED**

## Scope / correction to v27

V27 validated on-browser inference of the **photographic** MediaPipe Selfie Multiclass ONNX 6-class model and Pose Lite on Kyoko, Noel, Ririka. Visual semantic QA failed: Noel and Ririka had clothing false positives in hair, all Pose Lite tracks unavailable and Kyoko had no confident clothing/hair observations. All v27 candidates remain UNBOUND.

V28 evaluates **anime-domain alternatives** and the previously acquired REAL AnimeSeg GC001 sample without spending RAM/GPU on duplicate heavy inference. This is a feasibility/quality research gate; it does **not** claim an anime-domain model runs in the browser or that arm/cloth semantic binding works.

## Sources and exact chain of custody

Existing SA10.27 research used the genuine original GC001/Kyoko image and a precomputed AnimeSeg v3 Mask2Former output:

- Source: C:/Work/Temp/macro-gc001/GC001_source.png
- Source SHA-256: 75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e
- Same exact source bytes appear as Kyoko/source.png in frozen v27 reference ZIP, not merely visual similarity.
- Existing isolated observer: C:/Work/Temp/sa1026-animeseg-gc001-v457/animeseg_mask.png
- Cached existing observer PNG SHA-256: ea1be2ff34d3bdbef5693ab3dbe1c60363fe6365cb42454829b96994f3520148
- Weight source: suzukimain/AnimeSeg, models/anime_seg_mask2former_v3.safetensors; **cached file** size 431643704 bytes and streamed SHA-256 **f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394**. Local cache revision directory c96402281c15e7761392012ec04f171ec884866f. No new weight download/replacement.
- Frozen v27 study ZIP: v27_stages_metrics.zip SHA-256 91b9f3851622feb55169bbf301b9dbb52d81036c260ea7e8f88fd7814423bd39.
- Actual isolated Python AnimeSeg v3 result was acquired previously; it was **not rerun** in v28.

The 12 classes are: background, skin, face, hair_main, left_eye, right_eye, left_eyebrow, right_eyebrow, nose, mouth, clothes, accessory. They **DO NOT** contain left_arm/right_arm labels. The masks have the documented exact 12-color palette and a 340x340 source-aligned raster.

## Quantitative comparison and visual interpretation

The real cached Kyoko output reports 19,637 source-opaque hair pixels and 16,223 source-opaque clothes pixels. In the prior v27 **accepted-class visualization**, **zero** hair and **zero** clothes pixels were accepted for Kyoko. That output's black includes both background and UNCLASSIFIED, so the 19,637 overlapping black cells **MUST NOT** be described as an actual incorrect model background classification.

Visual inspection of a fixed 5-column original/Facet/v27-class/AnimeSeg12/anime overlay:
- AnimeSeg separates the orange long hair, garment mass and large facial/skin regions on Kyoko substantially better than the accepted v27 six-class mask.
- Goggles/hat/accessories are overly broad and merged in the 12-class map, not reliable precise identity boundaries.
- The stored AnimeSeg mask is observation only, not independently annotated ground truth. No automatic region promotion, no reintroduced eyes or facial internals, no output modification.
- Noel and Ririka: **no verified source-aligned AnimeSeg v3 masks available**. V27 evidence is available but that does not establish accuracy of an anime parser. Their cross-model scores are NOT fabricated or extrapolated.

Source alpha >=255 is used when comparing confirmed opaque pixels, and the entire analysis is read-only. No altered Facet PNG was emitted by the study.

## Browser-runtime feasibility decision

AnimeSeg v3 source checkpoint is 431.6MB (decimal); cached research runtime is Python torch/transformers using Mask2Former. The checked non-local BrowserFallback tree contains a bundled ONNX Runtime WASM and a 4.57MB U2NetP ONNX, but **no validated browser ONNX export of the 12-class Mask2Former**, no established supported opset or JS pre/postprocessing parity, and no Chrome memory and runtime benchmark.

The PC had approximately 2.0GB free physical RAM when inspected. To avoid interrupting other projects (Qwen and other workloads), no new 432MB torch model inference, heavyweight ONNX conversion, OS adjustment or package installation was attempted. **This does NOT prove the model cannot run in browser**; it only means that gate is not satisfied.

Other options surveyed:
- SkyTNT/ISNet and BritishWerewolf/IS-Net-Anime ONNX classify subject versus background only; they do not supply garment/arm taxonomy.
- Faor-Mati/anime-character-segmentation includes ONNX foreground/character-mask models (large, source categories need independent checks). No verified semantic arm/garment classes in these references.
- VioletXF/manga-character-parts-coreml contains a 19-class Core ML parser and separate ONNX foreground/head components, but the Core ML part package is not a WASM/ONNX browser parser and separate license/compatibility validation is required.
- v3's available Mask2Former safetensors is the most directly relevant **semantic** reference in this project; do not silently replace it with a binary foreground segmenter.

## Research implementation

- tools/analyze_browser_anime_v28.py: SHA-pinned exact image/mask/v27 source comparison, class confusion, normalized original overlay, SHA-rich stage.json/metrics.json/preview.png. Bad source, mask, archive, checkpoint size or category RGB fails closed.
- tools/package_browser_anime_v28.py: builds read-only observed image/palette/metric package and explicitly records missing Noel/Ririka and browser gate HOLD.
- tests/test_browser_anime_feasibility_v28.py: 5 contract tests, failed-source check, model taxonomy, non-render interface, evidence provenance.
- Inherited browser research workflow and v27 tests remain intact. CI only installs Pillow for diagnostic package/tests; **no production dependency was added**.

## Promotion/next-phase gates

V28 feasibility **CLOSED AS HOLD**, not an accepted semantic renderer. Do not merge the stacked research PR to main or use the cached anime mask as UI runtime input in production.

Next (v29) needs:
1. Independent AnimeSeg v3 masks for Noel and Ririka from a memory-safe verified compute environment, plus at least one unseen holdout; original source hashes and provenance MUST match. No protected GC001 holdout leakage.
2. A manually reviewed false-positive matrix for hair versus clothes and distinct accessories, with calibration uncertainty; mask outputs remain unbound where unsupported.
3. Reliable anime-specific pose/arm keypoints independent from the 12-class parser, and explicit left/right limb graph corroboration.
4. Only after these evidence gates: explore source SHA-pinned browser ONNX conversion and test Chrome WASM memory, timing, mask parity and small-screen use. Reject if risky or too slow; do not depend on local worker.
5. Preserve foreground silhouette/tie/sleeve/staff, intentionally omit facial internals from final Minimalizer and prohibit image generation.

## Persistence

Canonical private Google Drive path under chatGPT及びCodex用/Minimalizer:
AnimeModelFeasibilityV28_20261009 (folder link recorded in PR and result manifest after cloud verification).

Packages contain **only existing Kyoko source/outputs and metrics**, no 432MB checkpoint copy and no invented Noel/Ririka mask. Source code and handoff remain in this repository; this research branch is intentionally Draft/HOLD.
