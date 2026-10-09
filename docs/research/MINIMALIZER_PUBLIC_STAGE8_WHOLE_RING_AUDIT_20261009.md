# Stage8 whole-ring structural audit (2026-10-09)

Source: immutable SA10.34 signed original Stage8. Candidate source: previously signed, independently replay-verified relocation + block replacement research outputs. All private original/candidate polygon coordinates remain in user-approved Google Drive, not GitHub.

## Exact whole-ring redundancy check
Test removing existing complete rings individually using the **official single-call all-ring OpenCV filled even-odd raster**. Every removal must reproduce the owner's entire 340x340 *unguarded* original raster, and combined removals are separately checked. There is no image generation and no source original edit.

| Case | Input candidate | Whole-ring savings | Output candidate | Historical Stage8 cap |
|---|---:|---:|---:|---:|
| GC001 | 2,292 | 8 | **2,284** | 1,887 (FAIL by 397) |
| Raden | 1,412 | 3 | **1,409** | 1,412 (**candidate budget PASS**) |

GC001's residual dominant owners at input were hair 676, unbound 471, major_clothing 283, torso 188, head 154, neck 127 vertices. These are research contour counts, not authority to erase part content. Raden's input leaders were hair 355, major_clothing 275 and torso 231.

The final candidates were **independently revalidated** directly against the preserved original Stage8 11-owner scenes: each owner's official full unguarded binary raster was pixel-identical (0 changed), 8-connected component count and RETR_TREE hierarchy unchanged, primitive ID/owner/color/z identity retained. Raden candidate 1,409 is now 3 points under the historic cap but this does not rewrite the original signed historical Stage8 scene.

## Restrictions and next gates

Full SVG browser parity at DPR1/DPR4, original source ROI RGB/shape quality, 40-shape full-scene, face-parts hidden, iPhone Safari and human Golden are still **NOT passed**. The GC001 cap remains FAIL. The candidate scenes are research-only; no merge or production rollout authorized.

Scripts: `tools/research/public_geometry_js/stage8_structural_inventory.py`, `stage8_whole_ring_probe.py`. Private revalidation under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_RingStructuralAudit_20261009`.
