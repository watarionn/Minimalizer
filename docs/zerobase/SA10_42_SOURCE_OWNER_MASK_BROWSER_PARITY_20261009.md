# SA10.42: Source-signed owner and protected SVG raster parity (2026-10-09)

**Decision: face + left/right arm exact original-source raster parity demonstrated in real Chromium, research PASS. Full-character release NO-GO.** This is a browser rendering semantics diagnostic, not a new segmentation model and not deployable.

## Why

[PR #287](https://github.com/watarionn/Minimalizer/pull/287) established that GC001 visor self-mask overlap does not independently prove source semantics. [PR #288](https://github.com/watarionn/Minimalizer/pull/288) showed original RGB error on an independently frozen Raden case and prohibited GC001 color gate transfer. SA10.41 had previously shown real Chrome SVG masks were not equivalent to OpenCV inclusive rasterized source boundaries (Raden: face 122, left arm 237, right arm 255 and whole scene 2,681 RGB-mismatched pixels). That is the precise SA10.42 problem addressed here.

## Frozen authority and independent reconstruction

Real input from the canonical SA10.34 / SA10.41 Google Drive research archives:

- Source `Raden_source.png`: SHA-256 `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`.
- Original Stage8 signed 11-owner contour JSON: SHA-256 `be6001f3607466617a4c2db92cdc92ad81296a403cdeeef009ac0628dc149b5f`.
- Original SA10.41 SVG: SHA-256 `ecc48fcf20a85b584a421bbd7f485c40c1c0bab6cd536049a73a61d4d7ac97db`.
- OpenCV signed full-scene reference: SHA-256 `749fc372e293de4a839b13dc2196d5576e98d2f5c784d73449ca2f96ab074a92`.
- Original signed face, left/right arm masks also individually SHA checked (see new tool's immutable `SIGNED` map).

The research tool reconstructs each Stage8 mask with the **same single `cv2.drawContours(FILLED, LINE_8)` call over depth-ordered signed rings**, including holes and one/two-point contours. It does not infer geometry from Chrome output or from a screenshot.

It renders original SVG mask definitions in **actual Chromium 144.0.7559.96** using Playwright and compares each isolated mask against that independently reconstructed source bitmap. Unlike a visual-only comparison, binary mask parity is measured first, then the complete signed full-character reference image is used for final RGB parity.

## Independent isolated source-owner observations

| Original owner | Signed OpenCV mask size | SVG missing pixels | SVG outside pixels | Experimental exact-mask replay |
| --- | ---: | ---: | ---: | ---: |
| Hair | 19,503 | 714 | 0 | 0 mismatch |
| Right arm | 9,872 | 257 | 0 | 0 mismatch |
| Left arm | 10,419 | 237 | 0 | 0 mismatch |
| Unknown | 447 | 82 | 0 | 0 mismatch |
| Face | 4,052 | 122 | 0 | 0 mismatch |

These are isolated **raster geometry** comparisons; neither Canny proximity nor source material classification is being passed as an anatomical label. All five baseline owner masks were visibly underfilled relative to OpenCV. In the same browser and with no change to source masks, run-length-consolidated pixel-cell rectangles provide an exact geometric replay. This is a proof-of-cause and deliberately counts its full cost.

## Final full-scene protected source pixel results

Only four masks were replaced in an isolated copy of the original SA10.41 SVG: final face guard, inverse face+arms protection, original right-arm source-owner mask, original left-arm source-owner mask. **All 11 owner z-order positions and unchanged original owner paint/color remain exactly as before.**

| Actual Chrome against signed OpenCV | Baseline | Research repair |
| --- | ---: | ---: |
| Face mismatching RGB pixels | 122 | **0** |
| Left arm | 237 | **0** |
| Right arm | 255 | **0** |
| Whole 340×340 scene | 2,681 | **2,065** |
| Whole-scene absolute RGB error | 3.911358 | **3.080646** |

Also, all four isolated definitions achieve exact binary parity:

- Face guard: 122 to 0 (53 pixel rectangles / 212 rectangle vertex occurrences)
- Inverse protection: 613 to 0 (280 rectangles / 1,120 vertices)
- Right-arm original owner: 257 to 0 (95 rectangles / 380 vertices)
- Left-arm original owner: 237 to 0 (132 rectangles / 528 vertices)

**Do not misread the zero protected-region RGB differences as a Golden PASS.** At least 2,065 whole-scene pixels still differ from the signed OpenCV preview, and the source itself still has unresolved face-visibility/clothing/arm quality issues beyond raster parity.

## Hard blocker: vertex budget

Original Raden source signed ring vertices = **2,370**, while the immutable original source budget is **1,412**. The four experimental mask definitions alone contain **560 rectangles, 2,240 counted vertex occurrences**, before accounting for other retained original SVG structures. This is a diagnostic exact replay, **not** an authorized optimization or an approved new production format. No hard threshold is relaxed or quietly ignored.

No image generation, inferred eyes/nose/mouth, source-raster SVG `<image>`, generative fill, original source replacement, production Local/Public/Worker changes, or other source owner material reconstruction was performed.

## Code, regression, and preservation

- `tools/research/sa1042_source_owner_mask_parity.py`: SHA-gated input, exact OpenCV ring replay, isolated Chrome geometry verification, four-mask research replay, real full-scene RGB comparisons, artifact manifests, fail-closed release flags.
- `tests/zerobase/test_sa1042_source_owner_mask_parity.py`: pure pixel-run decomposition, source holes/singleton, no raster embedding, bad SHA, real pixel mismatch scope and hard-gate regressions.
- Local independent algorithm test run: **6 tests PASS**. Actual Raden Chromium trial: verified four masks binary exact and final face/left/right signed RGB exact. This is not an assertion of final GitHub Actions CI status.
- Numeric report: [SA10.42 evidence JSON](evidence/sa1042_raden_exact_owner_mask_browser_20261009.json).
- Source SVG, actual browser before/after PNGs, comparison image and reproducibility metrics, including output SHA hashes: private approved [Google Drive SA10.42 folder](https://drive.google.com/drive/folders/1_Q5LeaVAHfd0jkz0Pae_rnLnjskfQIMM) under **`chatGPT及びCodex用/Minimalizer`**. The complete source execution artifacts are in `SA1042_research_outputs.zip`, individual before/after and comparison PNGs alongside it.

Run again after copying the seven unchanged signed inputs named in `SIGNED` to one directory:

```bash
python tools/research/sa1042_source_owner_mask_parity.py --root /path/to/signed_inputs --out /path/to/isolated_outputs --chromium /path/to/chromium
python -m pytest -q tests/zerobase/test_sa1042_source_owner_mask_parity.py
```

## Next

Seek a **budget-preserving SVG source-boundary representation**, with no global contour dilation, invented skin planes or moved signed silhouette. Extend identical independent pixel probes to hair, unknown and garment owners and test protected z-overdraw; then seek whole-scene Golden evidence and a genuinely independent positive apparel subject. Until vertex+whole-source+human Golden gates pass, **research PASS only, production NO-GO**.
