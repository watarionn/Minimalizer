# MinimalizerPublic Clipper2-WASM source-owner intersection trial (2026-10-09)

## Place in roadmap and strict scope
- Eighth isolated browser library trial after #344 polygon-clipping, #345 Simplify.js, #346 Delaunator, #347 Earcut, #348 SVGPathCommander, #349 SVGO and #350 resvg-WASM.
- User's remaining sequence: **Clipper2-WASM → VTracer**. This work completes only the Clipper2-WASM installation trial.
- Existing source-owner shapes, face non-display policy, image palette, geometry and output PNG/SVG are **never modified**. No generated or inferred image content. MinimalizerLocal and Python worker unchanged. No website deployment. This library trial cannot pass Golden/Stage8/Safari production gates.

## Upstream, vendor and license
- Official `clipper2-wasm@0.4.0` (BSL-1.0), from upstream `ErikSom/Clipper2-WASM`; actual package downloaded by `npm pack`.
- Official npm tar SHA-256: `22b3afe094024bd1c864bc30fbcaf9ce8919b294788c935a59bbda8dc9d5f158`.
- `dist/es/clipper2z.js` self-hosted byte-for-byte as `web/static/vendor/clipper2-wasm/clipper2z.mjs` (renamed extension only); `dist/es/clipper2z.wasm` unchanged at matching self-hosted path. WASM SHA-256: `429e866b4d7813cabfa7d31e6650825343109fb7d7a1702c533e8597573449ec`. Official package metadata and upstream Boost 1.0 LICENSE/THIRD_PARTY provenance retained. The npm artifact contains no own LICENSE file.
- `?publicClipper2Research=1` alone triggers dynamic ESM import + same-origin WASM init. Default Public and Local never import it; no CDN, worker connection or upload.

## Audit architecture
- Conservative, read-only `Intersect64` operation: each existing source owner's **entire** original even-odd ring set is passed through Clipper2's real WASM polygon intersection with the original image viewport.
- Input integer scale 256, with explicit exact representability: any coordinate that cannot be represented *exactly* on this grid is skipped instead of silently rounded. Closed duplicate endpoints normalized on a copy only, not in source owner. Whole owner included or skipped; no partial hole sets.
- Strict caps: 8 evaluated owners, 48 rings, 1600 source vertices, 160000 work pixels, 128 result rings, 3600 result vertices; malformed and oversized data fail closed or produce truncated audit.
- Each candidate is verified against the **full original owner** using the existing OpenCV-compatible `MinimalizerOpenCvRaster.rasterizeLoops(..., scale=2)` at work resolution. Only bit-for-bit mask equality counts `exactShapes`; mismatch increments `rejectedShapes` and records `rasterDifferentPixels`. Even exactly matching candidates are never used for output. All audit results expose `applied:false`.
- Normal original PNG/SVG creation and owner colors are unmodified; observer is called only after shapes already exist. Invalid/missing WASM/raster fails the audit but not the normal converter.
- Headers: `X-Minimalizer-Public-Clipper2-Audit`, `...-Exact-Shapes`, `...-Rejected-Shapes`, `...-Different-Pixels`; detailed counters in optional runtime metadata.

## Independently executed tests
- `node tests/js/test_public_clipper2_research.mjs`: **9 scenarios PASS** using actual official .wasm, intersection rectangle, viewport crossing, hole even-odd, source immutable, invalid/non-exact-grid input fail closed, 8-shape cap, no source raster, and **deliberately falsified candidate pixel negative control** correctly rejected.
- `python -m pytest tests/test_public_clipper2_research.py tests/test_public_resvg_research.py tests/test_public_svgo_research.py tests/test_public_svgpath_research.py tests/test_public_earcut_research.py tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **35 PASS** including static bundling / Local isolation. JS syntax: PASS.
- Independent real desktop Chrome fixture (`tests/fixtures/public_clipper2_browser_smoke.html`) via reusable Chrome CDP script: **2 shapes, 3 rings, 12 vertices**, hole and viewport-crossing rectangle, `exactShapes=2`, `rejectedShapes=0`, `rasterDifferentPixels=0`, `applied=false`, status `ok`.
- Real built Public static site (separate disposable smoke copy) through actual `MinimalizerComputeRoute.minimalize(file)`; reproducible `python scripts/smoke_public_clipper2_chrome.py`:
  - Default: HTTP 200, 24 final shapes, polygon diagnostic `ok`, Clipper2 `disabled`.
  - `?publicClipper2Research=1`: HTTP 200, 24 final shapes, `truncated` at 8-shape cap, 8 exact owners, 0 rejected, 0 differing mask pixels, polygon diagnostic still `ok`.
  - Both return the same **401-byte PNG** with identical SHA-256 `cbbc690b29687ccf9940fcaa1364df909e18b4850c66e745246c7df273f76150`. Subject model stub disabled only in disposable test build, not shipped public code.
- CI failures not caused by this PR (if any) must be examined and recorded separately, never reported as CI passing.

## Unresolved product/release checks
- This verifies bounded synthetic browser execution and source-owner diagnostic noninterference only. **It does not guarantee all 24 shapes**, actual signed Kyoko/Raden source parity, Stage8 vertex budgets, source color reconstruction, output SVG fidelity, iPhone Safari/DPR, complete legal notices, or website release readiness.
- Full third-party/legal attribution review before public deployment. No production build changes or automatic application of intersection candidates.
- **Next and last remaining library trial: VTracer.**
