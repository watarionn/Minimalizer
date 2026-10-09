# MinimalizerPublic: SVGO browser opt-in trial (2026-10-09)

## Baseline and scope
- This is the sixth isolated MinimalizerPublic browser library trial after merged #344 polygon-clipping, #345 Simplify.js, #346 Delaunator, #347 Earcut, and #348 SVGPathCommander.
- User's planned remaining order: **SVGO → resvg-wasm → Clipper2-WASM → VTracer**. Only SVGO is in this change.
- Does not modify MinimalizerLocal/Python, output colors, source ownership, silhouette, face policy, output geometry or product-quality gates. Does not deploy to website.
- Real upstream `svgo@4.1.0` ESM browser bundle self-hosted at `web/static/vendor/svgo/svgo.browser.js` with upstream MIT LICENSE and provenance `THIRD_PARTY.md`. Official browser bundle is dynamically imported only in opted-in Public route, not on normal conversions.

## Design
- `?publicSvgoResearch=1` loads `public-svgo-research.mjs` and its genuine pinned SVGO browser module.
- Observer builds a temporary SVG from up to 8 existing ordered owner shapes, preserving exact RGB values, all loop holes, `fill-rule=evenodd`, viewBox, and original path points.
- SVGO is restricted to metadata/comments/empty attribute serializer cleanup plugins; no contour/shape/transform/color changes, no `preset-default` or geometry optimization. Candidate is generated twice to confirm deterministic bytes.
- Original temporary SVG and optimized temporary SVG are rasterized separately by the SAME browser native SVG renderer at the SAME work resolution. All RGBA channels of all pixels must match for `rasterExact=true`; otherwise candidate is rejected, saved bytes reported 0. This compares SVG-to-SVG, **not** SVG to existing Canvas/PNG, not DPR/Safari supersampling parity or original image quality.
- Observer always reports `applied=false`: candidate never substitutes the conversion PNG, SVG, palette, geometry, or render order.
- Caps: 8 shapes, 48 rings, 1600 ring vertices, 160k work pixels and 60k SVG path characters. Whole owners only, never omit a subset of holes. Reports `truncated` when capped. Malformed, unavailable, non-deterministic, raster errors, or image mismatch cannot pass the exact gate.
- Headers: `X-Minimalizer-Public-SVGO-Audit`, `...-Exact`, `...-Saved-Bytes`; detailed metrics in engine result metadata. Default remains `disabled`. No external CDN, inference service or image upload.

## Executed verification
1. Real `svgo.browser.js` imported under Node 26. `node tests/js/test_public_svgo_research.mjs`: **8 scenarios PASS**, including official optimizer, deterministic candidate byte reduction, holes/paint order, input immutability, malformed/bounded inputs, bit-exact RGBA diff, missing raster fail-closed, and no candidate application.
2. `python -m pytest tests/test_public_svgo_research.py tests/test_public_svgpath_research.py tests/test_public_earcut_research.py tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **27 PASS**, Public static package and Local separation included.
3. `node --check` for Public route, browser engine and research module: PASS.
4. Real Chrome, independent hole-containing 64×64 owner-ring fixture (`tests/fixtures/public_svgo_browser_smoke.html`): SVGO `status: ok`; SVG **248 → 206 bytes**, 42 saved; **0 RGBA-different pixels**; candidate still not applied.
5. Actual built Public static page and `MinimalizerComputeRoute.minimalize(file)` in real desktop Chrome, source-guidance disabled only within disposable smoke build (`python scripts/smoke_public_svgo_chrome.py`):
   - OFF: HTTP 200, **24 shapes**, audit `disabled`, polygon-clipping `ok`.
   - ON: HTTP 200, **24 shapes**, audit `truncated` (8-shape limit), `rasterExact=1`, **42 bytes saved** on the temporary diagnostic SVG; polygon-clipping `ok`.
   - Both returned 401-byte PNG with identical SHA-256 `cbbc690b29687ccf9940fcaa1364df909e18b4850c66e745246c7df273f76150`.
   - Chrome headless `--dump-dom` cold-start could exit before async conversion settled; automated harness retries the disposable browser run up to four times, never weakens output gate.
6. The prior CI #348 Browser Shape v14 issue was an unrelated historical document whitespace check, not SVGO result. Fresh PR CI must be separately reviewed.

## Remaining product / release boundaries
- Library installation test **does not pass** Golden (GC001/Raden), Stage8 vertex budget, genuine source image parity, Safari/iPhone DPR, visual review, or website release.
- Full bundled/transitive license and notice completeness requires an explicit compliance gate before distributing this experimental vendor bundle to a public site; the bundled SVGO MIT license alone is not enough.
- No output image change, automatic SVG optimization, or change to face rendering is authorized.
- Next *library* trial: **resvg-wasm**, independent SVG raster QA only. Preserve the exact opt-in and release boundaries.
