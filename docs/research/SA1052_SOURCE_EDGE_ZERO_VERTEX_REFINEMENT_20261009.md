# SA10.52: Source-observed face and material contour refinement with zero added SVG vertices

2026-10-09. **Research replay PASS on Raden and GC001; original Stage8 source ring gate FAIL, artistic visual Golden and production HOLD.**

## Goal

Improve the last SA10.51 signed original-derived facial color and clothing boundary paths **without exceeding either character's real expanded SVG vertex budget**, preserving immutable Stage04 face mask geometry, source-defined Stage9/37 colored clothing polygons, z-order, and both signed arms. Do not fabricate eyes/nose/mouth, use generated fills, embed a raster, or silently modify prior source/champion artifacts. Final evaluation must use original RGB pixels, not the frozen flat face RGB reference.

## Implementation

`tools/research/sa1052_source_edge_refinement.py` SHA-verifies both private original authority sets (Raden seven files and GC001 eight) through SA10.49/47 and pins the **actual SA10.51 private candidate SVG SHA-256**. Independently reproduces the signed SA10.51 Chrome rendering SHA for each PNG before optimization. It enumerates actual `M … L … Z` contours of the **existing** `data-sa1051-observed` paths, then tries four 1-pixel cardinal translations of each independent contour. Every proposal is rendered with *real Chromium* (340×340, DPR1). A change is committed only when the signed-original facial RGB MAE (or source-visible foreground MAE for apparel) decreases, forbidden pixels remain bit-identical to the original SA10.51 replay, and all original path vertex counts remain exactly fixed. For face contours the entire area outside the signed face mask is locked, including the arms; for material contours the signed face and both arms are locked. Two bounded passes for face, one for apparel; strict no-tie optimization. All prior medoid fill colors, actual source polygon contents, owner z-order and the exact mask XML are verified unchanged.

For independent diagnostics, take the signed source's grayscale Sobel magnitude >128 **inside the Stage04 face mask** and compare the original-source RGB MAE on those high-contrast pixels. This is an **edge-rich-pixel proxy**, not an eye/nose/mouth landmark detector or proof of recognizable facial anatomy. Do not present it as semantic facial accuracy.

## Actual signed-original Chromium results

| Metric (lower is better) | Raden SA10.51 | Raden SA10.52 | GC001 SA10.51 | GC001 SA10.52 |
|---|---:|---:|---:|---:|
| Expanded deployed SVG vertices | **1,412** | **1,412** | **1,882** | **1,882** |
| Strict geometry limit | 1,412 | **PASS** | 1,887 | **PASS** |
| Original source face-region RGB MAE | 35.793353 | **33.651530** | 29.404429 | **27.575788** |
| Original source-visible character RGB MAE | 27.929286 | **27.758737** | 44.728182 | **44.469572** |
| Face high-gradient source RGB MAE | 61.349614 | **56.423920** | 58.183425 | **55.156538** |
| Accepted 1px face translations | — | **18** | — | **22** |
| Accepted 1px apparel translations | — | **3** | — | **5** |
| Changed pixels in either signed arm | — | **0** | — | **0** |

**No new vertices, colors, raster embeddings, masks or non-source anatomical shapes.** Shape vertex count and the original signed source fill planes stay unchanged; coordinate values of already source-measured observed-detail paths alone move by at most 2px from their SA10.51 starting positions, in two 1px passes. Unchanged count includes 12 Stage9 original color polygon vertices for Raden, 55 Stage9/37 for GC001 and all remaining owner masks and trim corrections.

## Reproducibility and decision

- `tests/zerobase/test_sa1052_source_edge_refinement.py`: **8/8 PASS** using the signed Raden/GC001 sources and SHA-locked SA10.51 SVGs. Tests cover tampered original and SVG rejection, permitted 1px coordinate-only moves, immutable mask/palette/geometry inventory, source Sobel evidence, no-overwrite protections and full actual Chromium integrated replay.
- Two independent full Chromium evaluations produced **8/8 byte-identical SHA-256 artifacts** across all SVGs, PNGs, side-by-side comparison and JSON report. Per-contour 1px move trace and metrics are stored without original contour coordinates in public-safe `sa1052_metrics.json`.
- `chatGPT及びCodex用/Minimalizer/SA1052_SourceEdgeZeroVertexRefinement_20261009` in the user's Google Drive is the private source for produced SVG and original-containing PNG comparison, plus ZIP, code, tests, and reports. GitHub contains research code, tests, this report and **coordinate-free** metrics only.
- Visual review of the actual comparison image still identifies **disconnected/coarse face feature shapes, especially Raden's eyes**, missing nose/mouth microfeatures and hair/garment simplifications. Lower MAE is meaningful but small and **does not certify restored identity**. Original Stage8 2,370/1,412 and 3,604/1,887 ring gate both remain failed and are distinct from the deployed SVG gate. No human visual approval. **No Golden release, no production deployment**, and original champion SVGs remain immutable.

## Next stage SA10.53

Research **explicit original-2D anchored facial feature ROIs and garment part boundaries** with independently verified evidence and face silhouette locks. Evaluate eye/eyebrow/mouth position/shape on the original image, not an invented semantic landmark, and compare *actual two-case Chromium output* before/after. Reallocate real expanded vertices only with proven bitmap-equivalent substitutions or measurable source-fidelity improvements. Continue to fail closed on source Stage8 and human visual quality gates.

## Reproduce (private source and SA10.51 baseline SVG required)

```bash
python tools/research/sa1052_source_edge_refinement.py \
  --raden /private/signed/Raden --gc001 /private/signed/GC001 \
  --raden-svg /private/SA1051/raden_budget_detail.svg \
  --gc001-svg /private/SA1051/gc001_budget_detail.svg \
  --out /private/SA1052_run1
SA1052_RADEN_ROOT=/private/signed/Raden SA1052_GC001_ROOT=/private/signed/GC001 \
  SA1052_RADEN_BASELINE=/private/SA1051/raden_budget_detail.svg \
  SA1052_GC001_BASELINE=/private/SA1051/gc001_budget_detail.svg \
  python -m pytest -q tests/zerobase/test_sa1052_source_edge_refinement.py
```
