# MinimalizerPublic resvg-WASM independent SVG raster research (2026-10-09)

## Scope
This is the seventh isolated MinimalizerPublic JavaScript/WASM library introduction after polygon-clipping (#344), Simplify.js (#345), Delaunator (#346), Earcut (#347), SVGPathCommander (#348), and SVGO (#349).

Pinned official `@resvg/resvg-wasm@2.6.2` browser WASM (MPL-2.0) under `web/static/vendor/resvg-wasm`, with npm package metadata, unmodified index.mjs + index_bg.wasm, full upstream MPL license and SHA-256 provenance / source links in THIRD_PARTY.md. No external CDN and no Python/LocalWorker. Frontend imports `public-resvg-research.mjs` ONLY when `?publicResvgResearch=1`, and the WASM is fetched from its self-hosted same-origin path only at opt-in. Normal conversion never imports/fetches this ~2.48 MB WASM.

## Design / strict containment
- The observer builds a temporary SVG from the first up to 8 original owner shapes, preserving all whole-owner loops (including holes), source RGB, original path vertex order, original work pixel dimensions, the even-odd fill rule and original shape paint order.
- Caps: 8 shapes, 48 rings, 1600 vertices, max 160000 work pixels, 60000 path-coordinate chars. Any owner that would exceed a cap is skipped as a WHOLE; diagnostic reports `truncated`. No partial hole sets. Invalid values fail closed.
- Rust resvg-WASM independently rasterizes the temporary source SVG at original dimensions into PNG. Same Chrome separately rasterizes that source SVG. Compare all four byte channels of every decoded RGBA pixel; report differentPixels, maxChannelDelta, absoluteChannelDelta, exactNativeParity. This is an **independent browser-native-vs-resvg rendering discrepancy probe**, NOT a promise that the two engines always produce identical pixels. Nonzero pixels are reported, not silently accepted/replaced.
- The PNG returned to the user is always made by the **original Minimalizer browser converter**. The new PNG is *never* applied, exported, painted to the production canvas or adopted for source colors. All results explicitly `applied:false`. Failing/missing WASM does not fail the conversion.
- The experiment runs after the regular owner scene is computed; no changes to image pixels, owner masks, face policy, palette, SVG production or legacy Local/Python.
- Response headers `X-Minimalizer-Public-RESVG-Audit`, `...-Different-Pixels`, `...-Exact`; full metrics in engine metadata.

## Executed independent checks
- `node tests/js/test_public_resvg_research.mjs`: **6 scenarios PASS**, including genuine 2.6.2 WASM SVG→PNG with its unmodified ~2.48MB binary, signature PNG, hole preservation, source-order/RGB immutability, malformed/over-budget fail-closed, alpha-inclusive channel comparison, non-browser failure never applied.
- Real desktop Chrome via zero-dependency, repeatable CDP runner `node scripts/resvg_chrome_cdp.mjs http://127.0.0.1:8767/tests/fixtures/public_resvg_browser_smoke.html '#result'`: 64×64 image, source SVG 199 bytes, **2 owner rings**, resvg PNG 307 bytes, **0 different RGBA pixels** against Chrome SVG-native renderer; `status: ok`, `applied:false`. This is synthetic geometry.
- Real built Public static page with `MinimalizerComputeRoute.minimalize(file)` through **`python scripts/smoke_public_resvg_chrome.py`**: 64×64 controlled PNG, owner-guidance disabled *only in disposable browser smoke*, OFF and `?publicResvgResearch=1` ON each returned HTTP 200 PNG of **401 bytes**, **24 output shapes**, same SHA-256 `cbbc690b29687ccf9940fcaa1364df909e18b4850c66e745246c7df273f76150`; existing polygon-clipping audit `ok`; OFF status `disabled`, ON `truncated` (8-shape cap), **0 different pixels** on subset, exact flag 1. Remainder beyond cap has NOT been examined.
- Uses actual Chrome CDP `Runtime.evaluate` completion rather than brittle headless `--dump-dom` virtual-time timing. No extra installed npm packages.
- Combined Public/Local Python suite, JS syntax and static packaging must pass before PR. Check final PR body/CI for exact counts.

## Remaining release boundaries
- Full Golden GC001/Raden/Stage8 fidelity, SVG/PDF quality, product PNG/SVG parity, Safari/iPhone DPR, visual inspection and website deployment remain HOLD/separate. The diagnostic is not a product-quality PASS and must not change the official facial-feature non-display policy.
- MPL 2.0 source availability and transitive attribution compliance must be reviewed before shipping a public website containing the WASM; including upstream MPL license + provenance is necessary but NOT alone a final compliance sign-off.
- No production website release or source-image upload performed.
- Next independent library installation: **Clipper2-WASM**, then **VTracer**.
