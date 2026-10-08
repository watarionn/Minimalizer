# SA10.37: Clean apparel geometry and real Chrome SVG parity

Date: 2026-10-08 JST
Repository: `watarionn/Minimalizer`
Research branch: `research/sa1032-svg-contour-proposals`
Draft PR: #223, **DO NOT MERGE / DEPLOY**.

## Result and decision

**SA10.37 targeted geometry cleanup and verification: COMPLETE. Production: HOLD / NO-GO.**

The user liked the outer silhouette and wanted the interior apparel to be represented by fewer, cleaner geometric shapes. SA10.36 replaced a massive GC001 gray polygon with navy uniform, white shirt and a narrow green tie. SA10.37 **fixes its right navy region's previously self-intersecting outline** and reduces vertices of those same five source-grounded polygons, without redrawing the outer figure.

### GC001 verified outcome

| Invariant | Before (SA10.36) | SA10.37 result |
|---|---:|---:|
| Existing outer primitives | 11 | 11 |
| Existing added apparel color subpaths | 5 | 5 |
| Total apparel color-plane vertices | 36 | **27 (9 fewer, -25%)** |
| Self-intersecting apparel polygon(s) | index 1 | **none** |
| Source RGB lower-body Lab MSE | 4,606.609019 | **4,533.667405 (-1.5834%)** |
| Silhouette / original raw topology | preserved / PASS | **unchanged / PASS** |
| Existing face and left/right arm RGB | unchanged | **unchanged** |
| Necktie width / source area constraint | guarded | **guarded** |
| Extra geometry created | 0 | **0** |
| Source-color palette and owner identity | source-observed | **unchanged** |

Existing Phase8 adaptive outer contours and Phase9 source-color scene are SHA verified. The Stage36 five-panel vector file and preview are SHA verified, and the saved Phase36 preview is reproduced **pixel-for-pixel** before any edit. Geometry candidates are formed **only by removing existing polygon vertices**. Each candidate is scored by recomputing the entire five-plane material stack. The chosen result must retain original source-class coverage/precision, original palette, tie horizontal extent and source-based area cap, face/arms and off-owner RGB exactly, and stay within the original apparel Lab MSE +2% bound. The measured result actually improved color fidelity.

A bug/quality finding in the earlier stage: the right navy material was formed with a self-touching/intersecting contour in the signed SA10.36 candidate. The optimizer now detects this and **prioritizes its removal before cosmetic vertex pruning**, preventing the permitted error budget being consumed by less consequential edits. It refuses to promote output with remaining self intersections. This preserves the 5 material categories, not necessarily the full original pixel shape of every individual panel.

### Independent negative control: Juufuutei-Raden

The Raden image does not contain the distinctive source-observed dark/white/green uniform pattern, so no SA10.36 material planes existed. SA10.37 made **zero edits and saved a byte-for-byte identical RGB preview**. Raden's original source SHA is distinct from GC001. The two-image research validation **PASS**.

Each real-image run was independently repeated. Four output artifacts per case (metrics JSON, geometry JSON, preview PNG, 3-way comparison PNG) had **matching SHA256** across reruns.

## First actual Chrome SVG clipPath benchmark

A separate **all-vector SVG**, containing only the five garment polygons and their **existing Phase8 lower-body parent contour as clipPath**, was rendered in installed Chrome headless at 340×340. The SVG contains **no image, embedded PNG or base64 raster**. The independent reference uses the canonical OpenCV polygon clip. This is a deliberately isolated **apparel layer** parity check, not a full-browser scene certification.

A genuine Phase8 parent contour includes **one degenerate 1–2 point ring** that cannot be faithfully represented as an ordinary SVG filled polygon. The browser renders the major dark/white/green regions, but the exact pixel parity gate remains **FAIL**.

| Chrome raster setting | Different RGB pixels vs OpenCV | Pixels with RGB channel delta >48 |
|---|---:|---:|
| crispEdges, shift 0.0px | 568 | 431 |
| crispEdges, shift +0.25px | 558 | 396 |
| **crispEdges, shift +0.5px** | **528 (best observed)** | **388** |
| crispEdges, shift -0.5px | 1,018 | 745 |
| geometricPrecision, shift 0.0px | 1,123 | 627 |
| geometricPrecision, shift +0.5px | 974 | 547 |

The best option had mean absolute per-channel RGB difference 0.536459 across the 340×340 image. **Do not interpret low mean error as SVG exact parity**: 528 pixels are different, including 388 with large color differences, and the degenerate parent ring remains. No SVG geometric test was marked PASS. A difference heatmap and the actual Chrome screenshot were preserved.

No fake pixel overlay, base64 PNG SVG embedding, removal of raw topology constraints, or silent reclassification of protected/unknown owners was introduced to make the gate pass.

## Engineering and verification

New:
- `minimalizer_zerobase/reviewed_sa10/apparel_vertex_simplifier.py`: simple-polygon intersection validator and owner/source/tie-constrained vertex pruning.
- `tools/run_sa1037_apparel_simplified.py`: immutable source and parent artifact checks, 2 image runs, deterministic visual comparison.
- `tools/run_sa1037_crosscase.py`: independent SHA-qualified real-image research coverage with nonmatching image no-op.
- `tools/run_sa1037_browser_svg_probe.py`: pure-vector SVG parent clipPath and five fills, actual Chrome screenshot comparison with explicit hard fail.
- `tests/zerobase/test_sa1037_apparel_vertex_simplifier.py`, `test_sa1037_apparel_crosscase.py`, `test_sa1037_svg_browser_probe.py`: geometry and provenance regression tests.
- Research Actions workflow extended with these three tests and compilation of the tools.

The combined local targeted regression result: **97 passed, 7 parameterized subtests passed**. New SVG synthetic fixtures were corrected to use the actual lower-body owner schema; no core quality threshold was relaxed. GitHub Actions head status must be verified independently when reviewing PR #223.

Evidence:
- [GC001 apparel geometry metrics](evidence/sa1037_gc001_apparel_geometry_20261008.json)
- [Raden safe no-op metrics](evidence/sa1037_raden_apparel_geometry_20261008.json)
- [Two-real-source gate](evidence/sa1037_crosscase_apparel_geometry_20261008.json)
- [Actual Chrome baseline raster result](evidence/sa1037_gc001_browser_svg_zero_offset_20261008.json)
- [Actual Chrome best raster result](evidence/sa1037_gc001_browser_svg_halfpixel_20261008.json)

All comparison PNGs, geometry JSON, actual SVG, HTML, browser screenshot, OpenCV reference, difference heatmap and raster-setting evidence stored in
[Google Drive `chatGPT及びCodex用/Minimalizer/SA1037_Apparel_Vector_20261008`](https://drive.google.com/drive/folders/14WDUcyt6METuUleHYZvsMPgU-LZM9tJY).
Drive-mounted copies verified by SHA256.

## Non-negotiable release blockers

1. Existing Phase8 source-silhouette-preserving full vector ring vertex budget still **fails**: GC001 3,604 vs original limit 1,887; Raden 2,370 vs 1,412. The 27 apparel vertices are **extra** material subpaths, not hidden inside the old 11 primitive count.
2. Actual Chrome SVG parent clipping/output pixel parity **FAILS** (best 528 mismatched pixels plus one degenerate ring). Rendering a valid large shape in Chrome is not equivalent to preserving the source-defined raw boundary.
3. Human visual signoff still pending. Other internal apparel, hair and accents still need image-specific evaluation.
4. Results include two SHA-distinct images but the wardrobe grammar remains narrow; wider source datasets and a full product benchmark are not yet validated.

**Disposition:** The SA10.37 contour cleanup and an initial real Chrome SVG proof were executed, tested and preserved. The draft PR remains unmerged. Next step should solve browser-valid source topology with a true low-vertex representation and strict combined budget, or pursue further source-grounded internal accents without weakening the hard gates.
