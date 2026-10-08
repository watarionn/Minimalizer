# HND-20261008 SA10.39 → SA10.40

**Current repo** `watarionn/Minimalizer`, branch `research/sa1032-svg-contour-proposals`, DRAFT PR #223, **NO MERGE / NO DEPLOY**.

## User quality target
Outer silhouette already liked. Keep face detail simplified (no new eyes/mouth/nose), arm continuity, source semantic owners, narrow green tie, dark navy uniform and white shirt. All image changes must be source-observed low-vertex geometry, not img2img/generative fill/raster overlays. GitHub code is canonical; Drive binaries only under `chatGPT及びCodex用`. RDC only for actual Chrome/original local test images.

## Current verified results
- SA10.36: giant gray trapezoid in GC001 replaced by exactly **5 source-grounded apparel polygons** (navy x2, white x2, green tie x1); source MSE greatly improved.
- SA10.37: repaired one right-navy self-intersection and cut apparel **36 → 27 vertices**. Unrelated Raden has no matching uniform and stays byte-exactly unchanged.
- SA10.38: real Chrome headless, all-vector SVG luminance source-owner mask, original hole boundary strokes, no embedded raster. **528 → 69 RGB mismatched pixels** vs canonical OpenCV for isolated material layer. The single degenerate hole was omitted only after verifying zero authoritative owner mask changed pixels; Chrome executable/HTML/SVG/screenshot SHA attested.
- **SA10.39**: trace 69 mismatch pixels to material/source owner polygon boundaries. Add research opt-in **1.15px white parent contour stroke**, sourced from original existing rings, counted as **1 extra paint pass + 152 reused contour point occurrences**. Real Chrome **69 → 56 mismatched pixels (-18.8406%)**, still 45 severe; overall SA10.37 528 → 56 (-89.3939%). Of remaining 56, **50 are color-vs-blank, 6 colored-vs-colored**, **25** fall near both owner/material edges, **31** material only, **zero** farther than 1px-expanded edges. All source owner/garment geometry and 27 material vertices unchanged.
- Independent source Raden remains unmodified. `tools/run_sa1039_edge_research_gate.py` research gate **PASS**, production still strictly **NO-GO**.
- Per-material polygon line width changes individually did not outperform 56. Joint 36-combination calibration also failed to surpass 56. This is a GC001 340px raster calibration, NOT universally safe.
- Latest targeted 16 PASS plus 7 parameterized subtests, full SA10 research GitHub CI must be checked for the branch head before calling it successful.

## Exact code and docs
- `tools/run_sa1038_vector_mask_browser.py` option `--parent-outline-stroke`, default zero, bounded and counted.
- `tools/run_sa1039_svg_residual_audit.py` authoritative source/Chrome SHA validation and all-pixel attribution.
- `tools/run_sa1039_edge_research_gate.py` cross-image evidence.
- `tests/zerobase/test_sa1039_svg_residual_audit.py`
- `tests/zerobase/test_sa1039_edge_research_gate.py`
- `tests/zerobase/test_sa1038_vector_mask_browser.py` additional stroke accounting test.
- `docs/zerobase/SA10_39_CHROME_EDGE_ATTRIBUTION_20261008.md`
- JSON evidence: `docs/zerobase/evidence/sa1039_*.json`
- Google Drive visuals/Chrome screenshots/HTML/SVG/calibration and SHA manifest: https://drive.google.com/drive/folders/19Zj4LGJZhVeePFIj4KSJ3jLnbnGGF5js

## Nonnegotiable blockers
1. **Chrome browser exact parity still FAIL, 56 mismatched material-layer RGB pixels**.
2. Original **outer vertex budget FAIL**, GC001 3,604 >1,887 and Raden 2,370 >1,412, prior to all additional material/stroke geometry.
3. Tested only isolated material SVG, not complete scene, no second independently matching uniform case. Independent Raden is **nonmatching no-op control**, not a second positive Chrome test.
4. Human visual signoff not yet granted.

## SA10.40 next
- Move past GC001-specific subpixel stroke tuning. Evaluate actual vector rasterization topology and source-bound low-complexity geometry under *full global vertex budget* and improve the whole composed character's inner color panels and continuity.
- For 56 residual pixels, a clean visually stable geometric SVG might differ at antialias edges, but **do not relax an existing strict exact-pixel gate** unless a separately authorized formal spec change and evidence proves it appropriate.
- Add a second **matching** wardrobe source for positive generalization. Current Raden only a negative control.
- Implement complete source-signed scene SVG in real browser, checking face and both arms.
- Preserve any further evidence in GitHub + Drive; keep PR unmerged/no production.
