# MinimalizerPublic exact source-raster large contour vertex reduction (2026-10-09)

**Research proof-of-concept PASS for source owner pixel parity at 340×340. Historic Stage8 budget FAIL and production HOLD.**

With the unchanged SHA-frozen SA10.34 source Stage8 scenes, we used the original canonical `cv2.drawContours(canvas, depth-sorted-all-contours, -1, 255, cv2.FILLED, cv2.LINE_8)` rasterizer and tried removing *one vertex at a time* from source rings containing at least 4 points. The candidate removal was kept **only when every pixel of that entire owner's unguarded binary source mask was unchanged**. Every candidate is against the immutable owner's initial raster. This is not geometric approximation under a numeric-error tolerance; the required source-mask error is zero.

Eight thousand maximum trials per owner, all 11 owners per source case:

| Original | Stage8 source-ring vertices | Candidate | Raster-exact removed | Historic hard cap | Remaining gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| GC001 | 3,604 | **3,081** | **523** | 1,887 | 1,194 |
| Raden | 2,370 | **1,906** | **464** | 1,412 | 494 |

Private research derived Stage8 candidate JSONs were separately re-generated, serialized and SHA-pinned. The independent verification checks each owner's untouched original raw pixels, original 8-connected component counts and RETR_TREE hierarchy, original primitive ID, RGB palette, owner role and source-ring total. Zero source-owned pixel differences; no source JSON overwrite. Original full-body shape count, production gating, face feature hiding and painted RGB are untouched.

Public reproducibility files:
- `tools/research/public_geometry_js/stage8_large_ring_exact_reducer.py`
- `tools/research/public_geometry_js/stage8_large_ring_private_revalidation.py`

Private output under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_LargeRingExact_20261009`:
`GC001_stage8_candidate_PRIVATE.json`, `Raden_stage8_candidate_PRIVATE.json`, `stage8_large_ring_revalidation.json`.

**Critical limitations.** This guarantees the observed OpenCV source raster at 340×340, not vector curve/subpixel equivalence in Chrome, Safari, or the separate full-body 40-shape SVG. Candidate scene ring serialization may require further ring schema validation and its source provenance fields must be preserved. Existing historical Stage8 source ring caps remain failed. No production switch or merge is authorized. Human Golden HOLD.

Next: test larger search horizons, compare end-stage source geometry to known source pixel masks, capture exact candidate provenance, determine if source ring compression can meet the cap, and require independent SVG/DPR4 and original RGB non-regression before product promotion.
