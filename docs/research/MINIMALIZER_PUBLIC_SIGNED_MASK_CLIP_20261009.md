# MinimalizerPublic source-signed clip research (2026-10-09)

Status: **Chromium geometric gate PASS on two signed originals; complete product/quality gate HOLD**.

Starting point: draft PR #322, unchanged SA10.41 original images and SHA-verified Stage04 signed face and arm masks. No production source, API, LocalWorker or generated image change.

## Experiment
Run-length merged signed pixel-cell rectangles form an SVG clipPath around earlier Delaunator source-colored polygons. Every hole and disconnected mask component is preserved. Two variants: clip only, or add a uniform undercoat sampled from one actual RGB pixel of the verified source part (nearest pixel to signed part RGB mean). Face details remain hidden.

## Real Chromium 144.0.7559.96, DPR 4
| Signed original arm | Raw outside-alpha | Clipped outside-alpha | Undercoated coverage |
|---|---:|---:|---:|
| GC001 left | 0 | 0 | 100% |
| GC001 right | 10 | 0 | 100% |
| Raden left | 22 | 0 | 100% |
| Raden right | 7 | 0 | 100% |

Clipping alone does not solve missing interiors. In undercoat mode source-color masked 1x RGB error over white decreased, GC001 left/right 96.08 to 66.58 / 55.79 to 44.50 and Raden left/right 47.61 to 20.14 / 52.12 to 19.34. This metric does not certify appealing or minimal output.

## Hard shape gate
GC001 left/right need 111/108 clip rectangles plus 50/177 triangles. Raden left/right need 132/95 clip rectangles plus 293/253 triangles. Clip vertex occurrences alone are 444/432/528/380. **All violate the 40-shape prototype gate**; original source-ring vertex limits remain binding.

## Decision
Research-only vector-boundary approach demonstrated, no full-character Golden or production promotion. Remaining work: source-owned color-region simplification, primitive-budget reduction, full-character topology/z-order, multi-browser checks, and human visual review. Never reinterpret signed-mask raster parity as source anatomy or a permission to draw face parts.
