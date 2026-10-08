# BrowserFallback Geometry v13: prior art, decision, and validation gate

Date: 2026-10-08
Scope: **non-local BrowserFallback only**. This is NOT Minimalizer's Local Worker, zero-base SA10, or facial feature restoration.
Status: **EXPERIMENTAL BRANCH / REAL KYOKO IMAGE GATE NOT YET PASSED / DO NOT DEPLOY**.

## User-corrected visual target

Minimalize source images into a limited number of intentional geometric color fields.
**Omitting eyes, mouth, and nose is desirable.** Do not regenerate, redraw or preserve those features as a goal.
The attached Kyoko BrowserFallback result has wandering/jagged boundaries and blob-like color field silhouettes. First priority is polygon geometry and boundary clarity, not semantic detail.

## Prior art and feasibility

| Candidate | Source | Relevant insight | Decision |
| --- | --- | --- | --- |
| Mapshaper | https://github.com/mbloch/mapshaper | Weighted Visvalingam effective-area simplification, shared arcs, self-intersection repair; MPL-2.0 | Adopt algorithmic idea, not full mapshaper runtime. |
| TopoJSON Simplify | https://github.com/topojson/topojson-simplify | Simplify each shared arc once; ISC | Already structurally present in canonical-contour.js; no package. |
| Simplify.js | https://github.com/mourner/simplify-js | Fast RDP baseline; BSD-2-Clause | Existing OpenCV-like DP implementation already available; redundant. |
| ImageTracer.js | https://github.com/jankovicsandras/imagetracerjs | Browser-native raster-to-SVG, sharp/polygon presets; Unlicense | Hold: retracing the bitmap abandons current region graph and budgets. |
| VTracer | https://github.com/visioncortex/vtracer | Polygon mode, cutout/mosaic mode, WASM/Node build; MIT OR Apache-2.0 | Existing separate research. Do not switch BrowserFallback to an image-to-SVG pipeline without pixel/owner comparisons. |
| HF Spaces: ovi054/image-to-vector | https://huggingface.co/spaces/ovi054/image-to-vector | Python Gradio calling VTracer | Reference only; server-side runtime, no browser-self-hosted benefit. |

## Observed repository constraints

- BrowserFallback v12 is self-hosted static code, with no hosted image processing API.
- App defaults to Lite: `l0-lite-jacobi` + `legacy-independent-rings`.
- Exact opt-in: `spectral-exact` + `canonical-shared-chain` + `opencv-fillpoly-2x`.
- Current canonical contour candidate chain uses a Docker-independent OpenCV-like DP simplifier with endpoint anchors, shared edges, region IoU/area/centroid/directional gates, hole/component topology guards and intersection checks.
- The geometric improvement must use the same guards. **Do not weaken fidelity or topology constraints merely to reduce vertices.**

## Trial implementation (no external runtime package)

- `web/static/weighted-visvalingam.js`: standalone dependency-free weighted-triangle-area candidate; deterministic priority queue; only **removes interior vertices** and retains endpoints.
- `canonical-contour.js`: opt-in simplifier `weighted-visvalingam` or existing `opencv-dp` default. Every proposed chain still goes through existing shared-edge, topology and IoU candidate gates. Missing opt-in module fails closed.
- `app.js`: opt-in `?browserFallback=force&browserFallbackQuality=geo`; selects Exact structural profile and new geometry candidate.
- Existing normal `lite` and `exact` modes are not intended to change.
- Added output metadata `X-Minimalizer-Contour-Simplifier`, `contourSimplifier`.

**Not an algorithm installation from a third-party package**: research supports a tiny self-hosted implementation rather than bundling Mapshaper/TopoJSON and forcing a new build/runtime/dependency chain. The original code is independently implemented from the mathematical algorithm description.

## Validation before any merge/deploy

1. JS syntax for changed modules; focused Python/Node regression test.
2. `pytest tests/test_browser_geometry_v13.py tests/test_browser_fallback_v12.py -q`; compare existing tests.
3. Browser real execution on the same Kyoko source, at same dimensions and palette/shape budget, in `lite`, `exact`, `geo`. Record actual `contourSimplifier` headers.
4. Save independent output PNG/SVG, and 100%-zoom and 400%-zoom edge comparison. Record polygons, total vertices, mean/min region IoU, connected components and holes, processing time, roughness/jaggedness, geometric readability.
5. Compare all existing character regression cases. Reject candidate on worse contour artifacts, missing geometry, increased fragmentation, self-intersections, unacceptable time/memory.
6. Only then decide if experiment should become an opt-in public feature or a default; do not auto-merge or silently deploy.

**Production integration remains HOLD until visual and CI gates pass.** Research artifacts and code belong to GitHub; original user images are not committed to the public repository.
