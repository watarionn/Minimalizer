# MinimalizerPublic library installation: Earcut 3.2.4 (2026-10-09)

## Purpose and boundaries

The purpose of this chat is to install working **JavaScript/WASM libraries into MinimalizerPublic**, not to complete the independent MinimalizerPublic product and not to change MinimalizerLocal. Its Public browser page and route are `web/static/index.html` and `web/static/public-route.js` in `watarionn/Minimalizer`. The Local worker, Python dependencies and Local page are untouched.

Previous merged Public libraries:
- `polygon-clipping@0.15.7` (MIT): browser clipping/intersection audit, PR #344.
- `simplify-js@1.2.4` (BSD-2-Clause): source-mask-exact contour reduction research, PR #345.
- `delaunator@5.1.0` (ISC): Delaunay triangle research with source-ownership guard, PR #346.

New 4th library: **`earcut@3.2.4` (ISC)** self-hosted UMD browser bundle and license notice. Earcut is complementary to Delaunator: it can triangulate a valid source polygon **with an explicit set of holes**, rather than triangulating a flat point cloud without respecting holes. Its upstream documentation warns that self-crossing or invalid rings may yield incorrect triangulations. Our owner-mask gate is intentionally authoritative.

## Browser research integration

- Vendored official npm `dist/earcut.min.js` to `web/static/vendor/earcut/` with `LICENSE` and `THIRD_PARTY.md`.
- Public page loads the library and `public-earcut-research.js` before browser fallback; Local doesn't import the new files.
- Only `?publicEarcutResearch=1` opts in; normal conversions return a `disabled` diagnostic.
- From each unchanged source owner's current rings, passes flattened original source coordinates to Earcut, treating first ring as outer and remaining rings as proposed holes. The actual original OpenCV-compatible **full owner raster** is used as the authority.
- Every triangle candidate is separately rasterized with existing `MinimalizerOpenCvRaster.rasterizeLoops`. A triangle is counted as accepted only if it paints **no pixels outside the same original owner mask**. A fully reconstructed shape is reported only when the complete union of all accepted triangles exactly equals the original owner raster and the examination wasn't truncated. Detached/ambiguous rings fail the full reconstruction gate.
- Hard bounds: 8 shapes, 24 rings, 180 vertices, 64 candidate triangles, 160,000 work pixels. Truncation explicitly flags incomplete results. Missing libraries, malformed source data and raster errors fail closed. Rendering is never switched to Earcut and output PNGs/SVGs remain unchanged.

## Windows and browser verification

- Authentic npm 3.2.4 UMD loaded in JavaScript sandbox, exports real `earcut.default` function; a square triangulated correctly.
- `node tests/js/test_public_earcut_research.cjs`: **8 cases PASS**. Solid square -> 2 safe triangles and fully reconstructed exact mask; proper 1-hole square -> 8 safe triangles and a fully reconstructed exact mask; concave L-shaped polygon -> 4 safe triangles with original raster reconstruction; disconnected extra outer ring does **not** receive false full-reconstruction approval. Missing library, malformed inputs, caps and original-shape immutability checked.
- `pytest tests/test_public_earcut_research.py tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: 19 tests expected when the new vendor THIRD_PARTY.md is committed; exact final result to be recorded after rerun.
- Public built browser route test still required at this writing to verify identical normal vs research PNGs and true runtime metrics. Do not claim browser validation before observed.

## Scope limit

This is **library installation + safe candidate validation**, not actual triangular rendering, not proof of SVG DPR1/DPR4, source-colored Golden, mobile Safari or an overall MinimalizerPublic release. The separate product-completion chat owns those gates. No library should be claimed as improving output quality merely because it is now callable.
