# Minimalizer Local VTracer Demo Controls (2026-11-11)

Status: **Local PWA opt-in research UI only. No semantic owner / Golden / C08 / Public promotion.**

## Goal
Bring the classic VTracer browser demo's interactive controls into the already deployed private 5-Engine Lab. User's request: "vtracerのデモページでできることをやりたい". Keep the original two-engine comparison and external three-engine import modes intact.

## Boundaries
- VTracer source: pinned existing `web/static/vendor/vtracer-wasm/vtracer.mjs` + `vtracer.wasm` (`vtracer-wasm@0.1.0`, research-only bundle; existing incomplete dependency/license notice audit remains a separate release gate). The official 2026 VTracer 1.0 CLI contains **additional features unsupported by this pinned build**: watershed clustering, auto/fixed palette, adaptive B/W, spline simplification and updated optimization. None of these are falsely exposed in this phase.
- Classic demo upstream reference: `visioncortex/vtracer/webapp/app/index.html` at GitHub; controls and ranges are mirrored, plus an explicit 0..8 SVG coordinate precision advanced slider.
- Color / B&W, Stacked / Cutout (only displayed for Color), Pixel / Polygon / Spline, filter speckle 1..16, color precision 1..8, gradient step 0..255, corner threshold 0..180, segment length 3.5..10 step 0.5, splice threshold 0..180, coordinate precision 0..8.
- Defaults: Color / Stacked / Spline, speckle 4, precision 6, layer difference 16, corner 60, length 4, splice 45 and path precision 4. Defaults and validation implemented as pure JavaScript in `local_worker/frontend/vtracer-demo-options.mjs`.
- Changing control values updates labels and visibility immediately; selecting new values schedules a re-run if auto-update is checked (350ms debounce). An explicit **VTracer 実行** button is always available; reset restores defaults.
- The source resolution menu now supports 340 and 512 pixels in addition to 128, 192 and 256 to give the user access to less reduced character images. Existing max-dimension and 20MB checks remain; drawing work resolution never exceeds selected cap.
- The current settings are preserved alongside VTracer candidate metrics in the exported source-free comparison JSON. SVG export uses only the selected result.
- No server image upload, changed LocalWorker API, changed auth, changed PWA cache behavior, changed default Minimalizer conversion route, Public asset changes, semantic owner mask or Golden promotion.

## Validation
- `node --check` for both Local modules: PASS on owner PC.
- `node tests/js/test_local_vtracer_demo_options.mjs`: `LOCAL_VTRACER_DEMO_OPTIONS_PASS`.
- Owner PC protected venv `pytest tests/test_local_five_engine_lab.py tests/test_minimalizer_page_split.py tests/test_local_worker.py -q`: 22 passed before final static assertion was added.
- Disposable real Chrome/CDP with ephemeral loopback file server (`scripts/smoke_local_five_engine_lab_chrome.py`): `LOCAL_FIVE_ENGINE_CHROME_PASS`; VTracer default, Pixel Color/Stacked, Polygon Color/Cutout, Spline B/W all yielded real SVGs; paths differ between tested modes, B/W hides color-only controls and Reset restores the default. ImageTracerJS retained working output. No private source image.
- Pending before release: rerun final complete static suite, inspect the PR diff, merge, update owner production checkout and read back private HTTPS.

## Next milestone (separate)
Consider upgrading the WASM build to official 1.0 capabilities only after precise browser build/license/provenance audit; do not silently replace the pinned research binary or assert unsupported options.
