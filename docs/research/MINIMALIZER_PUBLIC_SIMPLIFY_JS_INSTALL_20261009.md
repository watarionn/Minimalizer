# MinimalizerPublic: Simplify.js library integration, source-exact proposal study (2026-10-09)

## Goal and Local/Public boundary

This chat's goal is to **install and validate useful libraries for MinimalizerPublic**. Full product completion, source Stage8 budget, human Golden, Safari and production deployment are managed separately. MinimalizerPublic is the browser-only page and compute route under `web/static`. MinimalizerLocal's Python worker and route are not modified.

Previous installation: browser `polygon-clipping@0.15.7` for actual viewport polygon diagnostics (PR #344, merged). This step installs real [Simplify.js](https://github.com/mourner/simplify-js) **v1.2.4** with BSD-2-Clause license as a pinned browser script under `web/static/vendor/simplify-js/`, with full license/attribution.

### Why this library

`polygon-clipping` provides polygon Boolean/intersection operations but is not a dedicated contour vertex simplifier. `simplify-js` implements Ramer–Douglas–Peucker line simplification with an optional radial-distance phase, and is a small direct JavaScript function without WASM loading. `clipper2-wasm@0.4.0` is a credible future candidate when polygon offsetting / Clipper2 boolean operations are genuinely needed, but a separate WASM loader and asset deployment would duplicate already available polygon-clipping diagnostics. Do not install Clipper2 just to claim a library count.

## Integration and safety

- `web/static/index.html`: loads vendored library and `public-simplify-research.js` before the existing browser engine; Public-only.
- `web/static/public-route.js`: explicitly sets `publicSimplifyResearch` true **only when the current URL has `?publicSimplifyResearch=1`**; normal requests default false.
- `web/static/browser-fallback.js`: optional research observer runs after original shapes and pixels were already rendered, reports headers `X-Minimalizer-Public-Simplify-Audit` and `X-Minimalizer-Public-Simplify-Safe-Vertices`. No proposed geometries are promoted.
- Research observer calls the original `MinimalizerOpenCvRaster.rasterizeLoops` on whole-owner rings before and after every Simplify.js proposal, accepting a candidate for **research counting only** if the complete owner binary mask is bitwise identical. This also protects holes. Proposals drop only original vertices, never synthesize material or facial parts.
- Guardrails: input under 160,000 pixels, up to 12 shapes, 48 actual proposals, ring size at most 1,200. Missing libraries/rasterizer return unavailable, invalid inputs fail closed, exceptions report error without aborting the image conversion. A truncated audit is *not* a full coverage certification.

## Verified real execution

- `node tests/js/test_public_simplify_research.cjs`: **6 scenarios PASS**. A synthetic rectangle with redundant points yielded **3 safe removed vertices**; three unsafe notch proposals were rejected. Whole-owner hole and input immutability tests PASS; bounded shapes and unavailable-library tests PASS.
- `pytest tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **11 PASS**.
- `node --check` on Public route, browser engine and new observer: PASS.
- Real Chrome on locally built `dist/shin` Public pages, `MinimalizerComputeRoute.minimalize(file)` with same synthetic 48×48 PNG:
  - Normal URL: `audit=disabled`, 24 output shapes, status 200.
  - `?publicSimplifyResearch=1`: `audit=truncated` (12-shape cap), **one additional safe research vertex** discovered, 24 output shapes, status 200.
  - PNG output SHA-256 **both paths exactly** `58111bef7bb783ddb4424856c918cbffb6a43b54070f941b83613f5018262f74` (357 bytes).
  - Existing `polygon-clipping` audit remained `ok` in both.
  - Browser subject model deliberately disabled **only for isolated library smoke**, not changed in application code.

## Scientific limitations and next candidates

This is a library installation + demonstrable fully exact **research proposal**. It is not a claim that Simplify.js improves production graphics, not a new Stage8 gate PASS, and not a Golden approval. The browser raster equality test is only at the Public renderer's native work size; it says nothing about browser SVG DPR4, hidden face details, source-semantic provenance or source RGB. The signed Stage8 original is owned by the separate product-completion process.

Library candidates for a subsequent installation: `clipper2-wasm` (only if offsetting/robust boolean operations prove valuable), `delaunator` (mesh topology/triangulation after source ownership gates), and browser-native SVG path support with no dependency if enough. Avoid duplicating the existing `polygon-clipping`/Simplify.js functionality.

**Release decision**: Browser library installed and opt-in active in code; normal images unchanged. GitHub merge is independent of deploying the production website, which remains the other chat's responsibility.
