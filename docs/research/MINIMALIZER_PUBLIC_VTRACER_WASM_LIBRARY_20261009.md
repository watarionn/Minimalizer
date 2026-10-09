# MinimalizerPublic VTracer browser-WASM audit (2026-10-09)

## Scope and library selection
- Ninth isolated browser-library research trial following #344 polygon-clipping, #345 Simplify.js, #346 Delaunator, #347 Earcut, #348 SVGPathCommander, #349 SVGO, #350 resvg-WASM, and #351 Clipper2-WASM.
- Official `@visioncortex/vtracer@1.0.0-alpha.4` is currently built for Node.js `wasm-pack --target nodejs` and uses Node-only filesystem glue. It was evaluated and NOT shipped.
- Browser-oriented `vtracer-wasm@0.1.0` from `jsscheller/vtracer-wasm`, based on VTracer, was selected as a **research-only** browser build (MIT wrapper, VTracer upstream MIT OR Apache-2.0).
- Unmodified npm package files: `vtracer.js` copied under `vtracer.mjs` extension, actual `vtracer.wasm` (136862 bytes), original LICENSE + package.json. Upstream VTracer license also preserved.
- Official npm archive SHA-256 `da0fe09e41ad0b9371453b22cdef73363381cbcb4f4c97ce2659f8db5a2a6f66`. Actual WASM SHA-256 `b93108af0f23e13a64f4b23f2582312a325be9d7ff833e49d04554cd99606f0b`.
- Detailed third-party sources and licensing reservations recorded at `web/static/vendor/vtracer-wasm/THIRD_PARTY.md`.

## Architecture: no product image changes
- `?publicVTracerResearch=1` is the only dynamic import / same-origin WASM fetch switch. Normal conversions do not execute VTracer and do not fetch its WASM. MinimalizerLocal and Python worker unchanged.
- The source to VTracer is **not the uploaded original photo**: it is a read-only sample of the current already-rendered MinimalizerPublic output canvas. Thus no new face, eye, mouth, or clothing source inference can be introduced through the observer.
- Bounded sample max side 96 pixels, max 9216 pixels. Large finished canvases are downsampled to this tiny research surface. This cannot certify native-resolution fidelity.
- Candidate SVG comes only from deterministic vectorization (not image generation). It is rasterized in a fresh, separate browser canvas. All four RGBA channels compared against the sampled existing Public result.
- Metrics: `changedPixels`, `comparedPixels`, `maxChannelDelta`, `absoluteChannelDelta`, `meanAbsChannelDelta`, `pixelExact`, sampled dimensions and `downsampled`.
- `status=exact` only when 0 pixel changes. Otherwise `pixel-mismatch` exposes a negative observation. Missing/WASM/runtime/malformed input is `error` or `invalid-input`, never a false pass.
- Candidate SVG strings are limited to 140000 chars and excluded when unexpected executable/external SVG markup is found.
- `applied=false` is invariant; the observer never returns its generated SVG to production code, changes owner masks, shape colors, paint ordering, exported PNG/SVG, or facial-feature non-display policy.

## Independent executed tests
- Official npm browser WASM `to_svg` runs in Node from vendored `.wasm` with all required config keys. `node tests/js/test_public_vtracer_research.mjs`: 8 scenarios PASS (genuine SVG conversion, deterministic repeated output, immutable RGBA, strict limits, alpha-inclusive byte comparison, unavailable canvas fail-closed).
- Public/Local integration and other browser-library regressions: `python -m pytest tests/test_public_vtracer_research.py tests/test_public_clipper2_research.py tests/test_public_resvg_research.py tests/test_public_svgo_research.py tests/test_public_svgpath_research.py tests/test_public_earcut_research.py tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`. See final executed result for count.
- Real desktop Chrome synthetic 64x64 fixture `tests/fixtures/public_vtracer_browser_smoke.html` using established reusable Chrome-CDP driver: `status=exact`, **0 different RGBA pixels / 4096 sample pixels**, SVG bytes 553, source output canvas untouched and candidate not applied.
- Actual built MinimalizerPublic (disposable Chrome smoke, original source guidance disabled only in the disposable test build) using `python scripts/smoke_public_vtracer_chrome.py`:
  - OFF HTTP 200, shapeCount 24, VTracer audit disabled, existing polygon-clipping audit ok.
  - ON HTTP 200, shapeCount 24, VTracer audit **pixel-mismatch**: **2 changed sample pixels**, exact flag 0. This is an honest loss: tracing does NOT pass strict pixel fidelity for this input.
  - OFF and ON returned byte-identical **401-byte PNG** with SHA-256 `cbbc690b29687ccf9940fcaa1364df909e18b4850c66e745246c7df273f76150`.
- Actual browser test uses CDP completion, not headless dump-dom timing. No additional npm dependencies installed on project.

## Release and continuation
- This is the last planned **library introduction** trial, not MinimalizerPublic completion.
- All new libraries remain research-only unless product-specific Golden/source-mask/Stage8/SVG quality gates are passed, with iPhone Safari/DPR, proper full notice/license source availability and final visual review performed separately.
- A 2-pixel VTracer difference is a **reject / HOLD** for any direct traced-SVG production substitution. Do not auto-adopt traced paths or silently claim source fidelity.
- Normal non-trial Public website is not deployed here. No remote image upload.
- After completion, the library research program can be handed to the separate product-quality integration workstream with evidence and limitations preserved.
