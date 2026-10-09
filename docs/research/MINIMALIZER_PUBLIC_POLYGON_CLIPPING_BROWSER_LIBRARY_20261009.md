# MinimalizerPublic: browser polygon-clipping integration and tests (2026-10-09)

## Boundary and intent

The user maintains **MinimalizerLocal and MinimalizerPublic as separate products/pages**. The repository records both under one GitHub repository, but the Public browser implementation is `web/static/index.html`, `public-route.js`, `browser-fallback.js` and files emitted by `scripts/build_shin_static.py`. Local's compute route remains `local_worker/frontend/local-route.js`, and neither Local's backend nor Python package dependencies were changed.

Python-only `pyclipper` installed in a prior stage was **not** an implementation of the browser Public product. This PR instead adds the genuine JavaScript MIT package `polygon-clipping@0.15.7` to Public as a pinned, self-hosted browser UMD bundle. `THIRD_PARTY.md` and the bundled `LICENSE.md` record provenance and attribution.

## Actual Public integration

1. `web/static/index.html` loads `vendor/polygon-clipping/polygon-clipping.umd.min.js` and `public-polygon-geometry.js` before Browser Fallback.
2. Only `public-route.js` opts into `publicPolygonDiagnostics: true`.
3. After the normal browser engine has rendered exactly the usual PNG, it passes the in-memory polygon rings to `MinimalizerPublicPolygonGeometry.auditShapes`. The library computes **real polygon intersections against the local work canvas viewport**, and returns aggregate clipping statistics without transmitting image bytes anywhere.
4. Bounded diagnostic checks: at most 160 rings and 12,000 vertices per conversion. Invalid/degenerate rings are skipped, clipping exceptions are counted and do not affect conversion; no geometry or color is replaced.
5. Public response exposes headers `X-Minimalizer-Public-Polygon-Audit` and `X-Minimalizer-Public-Polygon-Tested-Rings` to verify runtime use. Local has no opt-in and never loads the vendor bundle.

This is intentional **library integration for diagnostics**, not release of a new shape optimizer or replacement of the original OpenCV/canonical boundary pipeline. Future algorithm adoption must pass separate signed source-pixel/topology/Golden gates.

## Independent execution evidence

- Windows `node` verification of actual vendored clipping `intersection`: PASS; rectangular overlap results correct.
- `node tests/js/test_public_polygon_clipping.cjs`: 5 scenarios PASS (viewport intersection, outside viewport, degeneracy, geometry immutability, missing dependency).
- `python -m pytest tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **7 tests PASS**. Includes static builder copying UMD and license, and strict Local-vs-Public route isolation.
- `node --check` passed for vendor, Public adapter, Public route and the existing browser fallback.
- Chrome desktop browser, locally served **built Public static release** (`dist/shin`), 32x32 synthetic PNG, with browser subject model disabled only for the smoke: real Public page loaded, UMD `intersection` function available; full Browser Fallback conversion reported `X-Minimalizer-Public-Polygon-Audit: ok`, `X-Minimalizer-Public-Polygon-Tested-Rings: 16`, `X-Minimalizer-Shape-Count: 16`. Same input converted with diagnostic disabled returned a **bit-for-bit identical PNG blob** and `audit: disabled`. This is direct browser execution, not merely a mocked unit test.

## Remaining out of scope

This change is a library import/diagnostic introduction. MinimalizerPublic full-scene production completion, signed Stage8 remaining original vertex budgets, Golden visual validation, mobile iPhone Safari and any substantive geometric optimization remain in their **separate development effort**. Do not claim image-quality gains or that the new library automatically improves output quality. No server-side requests, Python runtime or local worker access are added. Do not deploy to production as part of this research PR without a separate release decision.
