# SA10.53: Visually sourced 2D facial ROI audit and zero-extra-vertex contour tuning

2026-10-09. **Real Chromium research PASS, two deployed SVG vertex budgets PASS; semantic identity / historical source Stage8 / human Golden and production remain HOLD.**

## Problem and truthful scope

SA10.52 reduced the full signed-original face RGB error, but a whole-face RGB score could hide severe errors in eye, eyebrow or mouth areas. An original 2D visual inspection of the two SHA-verified user-owned images established *approximate bounding regions* for the **image-left eye, image-right eye, image-left eyebrow, image-right eyebrow, and mouth**. Positions are stored as normalized signed-face bounding-box proportions, not private source pixel contours. They are manually visually anchored **hypotheses, not automatically detected anatomical landmarks**; signed face masks restrict the measured pixels, so partial eye/hair outside those masks cannot be evaluated with this gate. The ROI names indicate approximate screen positions, not verified anatomical detection.

ROI data is read from signed original photos, not the flattened Stage37 paint reference. Each ROI measures actual source-original RGB mean absolute error and, separately, original-image Sobel edge-rich (>128) pixel RGB error. These are localized RGB diagnostics and do not prove correct eye outline/iris/pupil, mouth topology, or identity. We refrain from a semantic facial feature PASS claim.

## Source-locked implementation

`tools/research/sa1053_feature_roi.py` verifies 7 immutable Raden and 8 immutable GC001 signed original files plus SHA-pinned SA10.52 baseline SVGs. It validates exact Chromium baseline original RGB errors before editing; the optimizer *only adjusts individual integer x/y coordinates on the previously existing three original-source face color feature paths*, moves of one cardinal pixel. Candidate vertices are those near a visual ROI, ranked by signed-source Sobel energy. Bounded search allows 5 vertices per screen-positioned eye, 5 around the mouth, 3 per eyebrow; four directions per vertex. Each candidate is rendered in full Chromium (340x340, DPR1) and retained only if its target ROI strictly improves, all other ROIs do not regress, the full signed-face original-source RGB MAE does not regress, and all pixels **outside the signed face** remain exactly equal to prior research. The final SVG path geometry inventory, mask structure, original pixel medoid colors, apparel Stage9/Stage37 colored polygons, z-order, signed face silhouette and actual expanded SVG vertex count are checked unchanged. No raster embedding, fill generation, hallucinated new eye/nose/mouth detail or source asset overwrite.

Only vertex-coordinate adjustments, no added paths, colors, vertices, mask references or shapes. This search does not claim that RGB error is sufficient for human identity.

## Observed signed-original Chromium results

| Measurement | Raden SA10.52 | Raden SA10.53 | GC001 SA10.52 | GC001 SA10.53 |
| --- | ---: | ---: | ---: | ---: |
| Expanded SVG geometry | 1,412 | **1,412** | 1,882 | **1,882** |
| Hard geometry cap | 1,412 | **PASS** | 1,887 | **PASS** |
| Original-source signed face RGB MAE | 33.651530 | **32.991774** | 27.575788 | **27.241105** |
| Original-source visible character RGB MAE | 27.758737 | **27.720248** | 44.469572 | **44.439580** |
| Annotated image-left eye RGB MAE | 34.251933 | **33.233743** | 37.508377 | **36.273369** |
| Annotated image-right eye RGB MAE | 35.357892 | **34.049715** | 35.906835 | **35.762505** |
| Annotated mouth RGB MAE | 13.893179 | **13.287001** | 4.446947 | **4.392893** |
| Accepted existing SVG vertex micro-moves | 0 | **15** | 0 | **8** |
| Full Chromium candidate renders | 0 | **84** | 0 | **72** |
| Signed left/right arm RGB pixels changed | 0 | **0** | 0 | **0** |
| Outside-signed-face RGB pixels changed | 0 | **0** | 0 | **0** |

Additional annotated brow values and source high-gradient error are recorded per ROI in JSON. All five regions' RGB errors non-increase; GC001 image-right brow is exactly tied, not claimed improved. All ROI RGB measurements compare original pixels and Chromium-rendered SVG, never a simulated scoring proxy. **No new SVG vertices.**

## Verification and preservation

- `tests/zerobase/test_sa1053_feature_roi.py`: **7/7 PASS** using both private sources and both frozen source-derived SA10.52 SVG baselines. Tests reject source or baseline tampering, check face clipped ROIs, negative position bounds, input/output isolation, actual two-character Chromium replay, geometry, and unchanged pixels outside signed face.
- Two independent fresh full Chromium runs produced **9/9 SHA-256 identical rendered images, SVGs, metrics JSON and two review comparison boards**. Chromium version and digest ledger are in `sa1053_metrics.json`.
- Google Drive private archive: `chatGPT及びCodex用/Minimalizer/SA1053_Original2DFacialROI_20261009`. Original image-inclusive comparison and actual candidate SVG geometry are preserved **only in approved private Drive**, not in public GitHub. GitHub receives source tool, tests, this report, and coordinate-free metrics; all previous champions unchanged.

## Gate

`TWO_CASE_SOURCE_AUTHORITY_PASS` / `REAL_CHROMIUM_SOURCE_ROI_AUDIT_PASS` / `TWO_CASE_BUDGET_PASS` / `TWO_CASE_SIGNED_FACE_MASK_SHAPE_AND_ARMS_PASS` / `SOURCE_COLOR_AND_POLYGON_PROVENANCE_PASS` / `SEMANTIC_LANDMARK_DETECTION_NOT_PERFORMED` / `HUMAN_VISUAL_REVIEW_PENDING` / `HISTORICAL_SOURCE_STAGE8_GATE_FAIL` / `GOLDEN_HOLD` / `PRODUCTION_UNCHANGED`.

The enlarged side-by-side face review still shows highly simplified/disconnected eyes, absent irises/pupil colors and under-resolved mouth and surrounding hair. The candidate is a research improvement, **not** finished face reconstruction. Original Stage8 source ring counts (Raden 2,370 / 1,412; GC001 3,604 / 1,887) remain above separate policy caps. No production or worker changes were made.

## Next SA10.54

Source-derived component-specific palette and contour conservation: evaluate small irises, eyelid dark/highlight pixels, mouth and hair boundaries with ROI-weighted structural evidence *and true expanded SVG costs*, choosing real source medoids only. Allocate vertices from demonstrably lower-salience visible owner polygons or eliminate source-proven no-op geometry with pixel-equivalence proof. Do not silently reassign color and do not infer new anatomy. Both characters' original fidelity and human review must pass before Golden release.

## Reproduce

```bash
python tools/research/sa1053_feature_roi.py \
  --raden /private/raden --gc001 /private/gc001 \
  --raden-svg /private/sa1052/raden_edge_refined.svg \
  --gc001-svg /private/sa1052/gc001_edge_refined.svg \
  --out /tmp/sa1053
SA1053_RADEN_ROOT=/private/raden SA1053_GC001_ROOT=/private/gc001 \
 SA1053_RADEN_BASE=/private/sa1052/raden_edge_refined.svg \
 SA1053_GC001_BASE=/private/sa1052/gc001_edge_refined.svg \
 python -m pytest -q tests/zerobase/test_sa1053_feature_roi.py
```
