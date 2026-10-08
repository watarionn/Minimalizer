# SA10.41: Full-character source-accurate replay and actual Chrome vector rendering

Date: **2026-10-08 JST**. Repository: `watarionn/Minimalizer`. Branch `research/sa1032-svg-contour-proposals`. Draft PR #223. **Research only, no merge/deploy.**

## Formal decision

**SA10.41 implementation, two complete source reconstructions, two real browser renders, regression tests, deterministic reruns and preservation: COMPLETE.**

**Actual complete-character SVG browser parity: FAIL**. Protected face and both arms: FAIL. Original source-ring and combined mask/material vertex budgets: FAIL. **Production NO-GO**.

The user approved the earlier *outer silhouette direction* and asked to improve the internal garments. It would be incorrect to promote the isolated apparel-layer raster progress (SA10.37 528→SA10.38 69→SA10.39 45→SA10.40 41 pixels) as if those measurements applied to a full figure. This phase closes that observability gap using an actual complete SVG scene and the original source PNGs.

## What was built

Full-vector renderer:
- `minimalizer_zerobase/reviewed_sa10/full_character_svg.py`
- `tools/run_sa1041_full_character_chrome.py`
- `tools/run_sa1041_full_scene_crosscase_gate.py`

Regression/CI:
- `tests/zerobase/test_sa1041_full_character_svg.py`
- `tests/zerobase/test_sa1041_full_scene_crosscase_gate.py`
- `.github/workflows/sa1032-svg-research.yml`

Unlike the earlier five-panel isolated browser probe, it replays **all 11 signed original Phase8 source owners** at their canonical source back-to-front z-order (10 painted, 1 structural support only). It also includes **the three GC001 Phase9 interior source-observed geometric color polygons** (torso/hair/major clothing), **the five GC001 signed Phase37 navy/white/thin-green-tie filled garment polygons** (27 extra material vertices), and a flat face guard equivalent to the deterministic Stage4 source face-mask color policy. Raden is a negative control with one Phase9 plane and zero navy/white/green apparel planes.

Only literal SVG geometry is emitted, not a copied source PNG, inlined `<image>`, base64 bitmap, Canvas pixel overlay, generative fill or fabricated eye/nose/mouth. Original ring geometry with length ≥3 becomes even-odd SVG path elements; source rings with one source point become explicitly counted 1px SVG rectangles and two-point rings become explicitly counted SVG lines. Source protected mask and flat face guard are vectorized directly from original Stage4 semantic masks, with their extra path-point occurrences counted. The SVG is experimental: even-odd SVG fill and degenerate micro-element paint passes are **not silently assumed equivalent** to OpenCV's single `cv2.drawContours(FILLED)` operation.

The original **OpenCV source pipeline was reconstructed first**, not inferred from a saved bitmap: all 11 real Phase8 rasterized owner masks, source-relative Phase9 plane clipping and z-order, original Stage4 face/left/right arm exclusion, source-observed face-flatten color guard, then 5 clipped Phase37 garment polygons. SHA verification ties Phase04/08/09/37 and original source bytes together. The reconstructed source RGB image for both cases was checked **pixel-for-pixel equal to the signed full-image Phase37 preview** before any browser execution. This is an actual reproducible baseline, not a claim that Chrome is correct.

## Actual two-character browser measurements

340×340 canvases, actual installed Chrome `--headless=new`, isolated profile, device pixel ratio 1; executable, HTML, SVG and screenshot SHA256 preserved.

| Quality and complexity | GC001 | Juufuutei-Raden |
|---|---:|---:|
| Independent original saved full preview reconstructed with OpenCV | **EXACT PASS** | **EXACT PASS** |
| Source owner records | 11 | 11 |
| Painted owners (excluding structural support) | 10 | 10 |
| Phase9 interior source-observed color planes | 3 | 1 |
| Phase37 apparel navy/white/green planes | 5 | 0 (correct no-op) |
| One- or two-point source contour rings | **110** | **13** |
| Signed original outer ring vertices | **3,604** | **2,370** |
| Original ring vertex upper limit | 1,887 | 1,412 |
| Combined SVG source/material/mask vertex occurrences | **4,312** | **2,976** |
| **Actual Chrome full-character RGB mismatched pixels** | **3,919** | **2,681** |
| Different pixels inside original source face mask | 140 | 122 |
| Different pixels inside original source left-arm mask | 206 | 237 |
| Different pixels inside original source right-arm mask | 199 | 255 |
| Real browser full character exact RGB parity | **FAIL** | **FAIL** |
| Face + both arms real browser boundary parity | **FAIL** | **FAIL** |
| Original/combined vertex-budget gate | **FAIL** | **FAIL** |

Source face errors were primarily low-channel color differences in this run (zero face-mask errors had channel delta >48), but **every** differing RGB pixel still violates exact parity. All 206 GC001 left-arm, 199 GC001 right-arm, 237 Raden left-arm, and 255 Raden right-arm differing pixels were high-channel errors (>48), clearly requiring geometry/owner clipping investigation. These are **browser comparisons inside original source masks**, not a claim that source anatomy or protected source data was modified.

GC001 and Raden original source SHA256 values differ and their observed clothing grammars differ. This demonstrates repeatable **full-scene rendering failure across two independent originals**, but Raden remains a **negative**, not a second independently positive matching-uniform candidate.

Every original geometry vertex, small component and additional rendered SVG stroke/path must be included in complexity; the 4,312/2,976 counts include repeated Stage4 protection and face mask point occurrences. Neither the 1,887 nor the 1,412 original total-vertex gate has been weakened.

## Authenticity, repeatability, gates

- Original source image, Stage04 mask PNG hashes, Phase8 adaptive scene hash/budget, Phase9 scene hash, Stage37 scene+final PNG hash: checked and source-dependent.
- Original whole-source candidate: **exact RGB reconstruction PASS** on both actual source images.
- Chrome source binary and full scene HTML/SVG, screenshot and decoded canvas checked; browser source `<image>` embedding explicitly prohibited.
- **Two independent actual Chrome runs per source produced 7/7 matching artifact SHA256 each**, including full rendered SVG, HTML, complete OpenCV reference, browser PNG, metrics, RGB difference heatmap and 3-way comparison.
- Two-original-image cross-case **research evidence gate PASS**, requiring actual nonzero Chrome errors and failing product parity status; it cannot turn two FAIL measurements into a product PASS.
- Extended local regression: **145 tests passed + 54 parameterized subtests passed**; source/tool Python compilation checked. Verify final GitHub Actions head run separately before declaring CI success.

Research evidence:
- [GC001 full-character real Chrome metrics](evidence/sa1041_gc001_full_character_chrome_20261008.json)
- [Raden full-character real Chrome metrics](evidence/sa1041_raden_full_character_chrome_20261008.json)
- [Source-distinct two-character explicit NO-GO gate](evidence/sa1041_two_source_full_character_gate_20261008.json)

Full SVG/HTML, original full-body source PNGs, true browser screenshot, authoritative OpenCV reference, three-way picture, pixel heatmap, protected-source original masks and the complete SHA manifest (**25 hash-verified source/visual artifacts**) are saved under:

**[Google Drive `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008`](https://drive.google.com/drive/folders/1-S22L7dMzs7tH32aLMel5bTSSsTQY7Oi)**.

## Failure analysis and safe next stage

SA10.41 exposes the genuine broader renderer gap: lots of source singleton/two-point rings, OpenCV inclusive hole boundaries, and nested SVG mask raster semantics affect hair, outer silhouette and left/right arms. The whole figure is visually related to the source but has many wrong edge/negative-space pixels, including protected owner areas. A lower overall RGB error obtained by thickening global parent contours would be unacceptable if it makes the signed silhouette worse, as earlier rejected SA10.39 experiments proved.

No additional source geometry, eyes, mouth, nose or apparel features were invented and no PNG was embedded into the SVG. Existing source RGB+geometry and production site were not changed.

**Next SA10.42:** per-original-owner real Chrome vector raster parity probes for face/arms/hair/unknown, with isolated owner-mask binary comparisons, signed original small-contour and hole restoration, plus post-z-order protected overlay certification. Investigate OpenCV vs SVG raster semantics systematically before generic repainting or microscopic garment tuning. Keep entire original/combined vertex budget hard, and seek another independent *positive* clothing case before release.

**SA10.41 engineering milestone complete. Product gate NO-GO. PR #223 remains draft, unmerged and not deployed.**
