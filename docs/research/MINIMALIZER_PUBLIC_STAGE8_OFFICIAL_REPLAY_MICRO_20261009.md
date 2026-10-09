# MinimalizerPublic Stage8 official renderer restoration and tiny-ring counterfactual (2026-10-09)

**Research exact pixel parity PASS. Vertex cap, production and human Golden remain HOLD.**

## Root cause of prior 4/11 and 7/11 parity failures
Official source code `minimalizer_zerobase/composition/semantic.py::rasterize_primitive_candidate` has a distinct ring raster contract: first sort all contours by **(depth, original index)** and then pass **all contours together to one cv2.drawContours(..., -1, 255, thickness=cv2.FILLED, lineType=cv2.LINE_8)**. OpenCV's even-odd fill handles holes and degeneracies. Drawing contours one-by-one and erasing holes is not the original renderer.

For *visible* source-owned masks, the official contour raster must then be AND-masked with original PNG alpha > 0. Every source PNG's SHA-256 and each source-visible owner mask's SHA-256 was independently verified against the frozen private manifest.

| Original | Official OpenCV raw contour vs visible mask exact owners | After source alpha > 0 guard | Discrepant source-transparent owner pixels |
|---|---:|---:|---:|
| GC001 | 10/11 | **11/11, 0 pixel difference** | 3 right-arm pixels |
| Raden | 10/11 | **11/11, 0 pixel difference** | 74 left-arm pixels |

## Micro-ring actual deletion counterfactual
With that exact renderer, test every 1-2-point source ring for *individual* deletion, compare to the original visible signed owner mask, and separately test all such individually safe rings deleted **together within each owner**.

| Original | Tested tiny rings | Individually exact deletions | Combined visible-mask parity | Sum of proposed removed ring vertices |
|---|---:|---:|---:|---:|
| GC001 | 110 | **13** | all 11/11 owners exact, zero altered pixels | **14** |
| Raden | 13 | **6** | all 11/11 owners exact, zero altered pixels | **9** |

This is a positive candidate-finding result **under exact original alpha-visible owner-mask pixel semantics**. The source files and production scenes were not modified. The fact that all owner binary mask pixels remain identical also preserves topology *at that exact measured visible 340x340 mask*, but full unguarded owner raster, semantic subpixel, Safari/browser SVG, and historic Stage8 provenance/output contract are separate checks still to be performed. No new RGB pixel or facial feature was generated. These 23 vertices cannot solve the original budget gaps GC001 +1,717 / Raden +958.

**Next:** measure unguarded source-owner binary mask parity for the 19 rings and whether hole hierarchy/source contour topology changes, DPR4 signed browser rendering, verify remaining original stage input invariants, then return to source-authorized geometry design for much larger vertex savings. Do not waive original Stage8 cap.
