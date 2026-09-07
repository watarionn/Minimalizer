# Minimalizer Handoff

## Restore order

1. Read `CURRENT.md`.
2. Read this file.
3. Read `README.md` and `REPOSITORY_LAYOUT.md`.
4. Treat `v0.3.0 stable` as the engine regression baseline.
5. Inspect the restored code and tests before changing behavior.

## Current state

Minimalizer v0.3.0 stable is complete, and its implementation snapshot has been restored into this GitHub repository. The original product goal remains simple: input image -> minimalized graphic. Core minimalization quality takes priority over optional character-specific features.

GitHub contains:
- `minimalize_engine/`, `app/`, `gui/` stable implementation source.
- the 39-file v0.3.0 stable regression suite plus Web Phase tests.
- `tests/assets/corpus/` with all 16 original regression images.
- `tests/assets/corpus_manifest.json` with the 16 corpus entries.
- `tools/` evaluation utilities.
- `examples/input.webp`, byte-identical to `tests/assets/corpus/Night-River-City_general.webp`.

Restoration sanity validation completed on GitHub Actions:
- 16/16 corpus entries exist.
- 39 stable test files exist.
- Night River original SHA-256 verified as `f244e86e02c90753ab575e0f95b5c872527afe0a63bb3c314b77a84c6ef81a66`.
- `examples/input.webp` and the Night River corpus file match that SHA.
- `compileall` passed for `minimalize_engine`, `app`, `gui`, `tools`, and `tests`.

Release validation recorded at v0.3.0:
- 156 tests passed / 0 failed when completed in batches.
- 16/16 corpus images processed successfully.
- Mean corpus quality about 0.7893.
- Mean identity about 0.9484.
- Mean silhouette about 0.9114.
- 8192x6373 (52.21 MP) stress input completed successfully.
- `compileall` passed.

A single-process full pytest run exceeded the interactive execution window and is not counted as a completed pass.

## Web Phase

Web Phase 1 established the FastAPI adapter. Web Phase 2 added the first browser workspace. Web Phase 3 adds production-readiness safeguards and generic deploy packaging without changing stable engine algorithms.

Current Web behavior:
- `GET /` serves the browser UI.
- `GET /api/info` reports Web/engine versions and current Web safety limits.
- `GET /health` provides a lightweight health check.
- `POST /api/minimalize` accepts one uploaded image through multipart form data.
- output formats: SVG and PNG.
- basic overrides: abstraction level, palette colors, target max shapes, and background mode.
- browser UI supports drag-and-drop/file selection, source/result side-by-side preview, processing/error/empty states, SVG download, PNG download, and responsive mobile layout.
- accepted source formats are PNG, JPEG, and WebP.
- upload size is capped at 20 MB.
- images are opened with Pillow before engine processing to validate real format and dimensions.
- Web limit is 64,000,000 total pixels and 16,384 pixels on either side.
- a process permits two simultaneous image-processing jobs; excess jobs receive HTTP 429 with `Retry-After: 2` rather than accumulating unbounded CPU work.
- basic security headers are returned; API/health responses use `Cache-Control: no-store`.
- Web runtime dependencies remain isolated from the PySide desktop GUI dependencies.
- `Dockerfile` provides a one-worker, non-root production container with a health check.
- `.dockerignore` excludes development/test material from the production image context.
- CI cancels superseded runs for the same ref and performs stable regressions, Web integration tests, and a real-Uvicorn server smoke request using `examples/input.webp`.

Run locally with:

```bash
python -m pip install -r requirements-web.txt
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Or with Docker:

```bash
docker build -t minimalizer-web .
docker run --rm -p 8000:8000 minimalizer-web
```

See `web/README.md` for browser/API usage and `docs/WEB_DEPLOYMENT.md` for hosting/sizing notes.

## Important stable behavior

- Conservative thin/noisy rectangle cleanup.
- Near-background fragment cleanup with semantic safeguards.
- Same-role union only when real contour connectivity is preserved.
- Experimental role-fragment merging remains OFF by default.
- Adaptive polygon simplification uses strict local raster IoU protection.
- Conservative polygon -> rectangle/ellipse promotion.
- Character identity and semantic geometry receive protection.
- Face primitive drawing is OFF by default.
- Advanced GUI controls are hidden by default.
- High-resolution RGB input preparation avoids an unnecessary eager full-size copy.

## Recommended next work

Web Phase 4 should be the first hosted pilot rather than another large local feature batch:
1. deploy the generic Docker image to an initial provider;
2. run real public-URL smoke tests for UI, health, SVG, and PNG;
3. measure peak memory and request duration with representative images;
4. exercise the 429 busy response under concurrent requests;
5. tune instance size, concurrency, and Web pixel limits from those measurements;
6. keep accounts/database/billing out until pilot usage demonstrates a need.

Current hosting evaluation (2026-09-07) favors Railway for the first low-traffic pilot because its Hobby plan starts with a small base commitment and usage-based resource billing. Render remains attractive when predictable always-on capacity is preferred. See `docs/WEB_DEPLOYMENT.md`; re-check provider pricing before deployment because hosting terms change.

Engine maintenance remains queued in parallel:
1. audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of `0.985` and add a regression test if needed;
2. add a fully opaque RGBA high-resolution smoke test;
3. improve weaker corpus cases without regressing the stable baseline.

Prefer `v0.3.1` for safe engine fixes and `v0.4.0` for broader algorithm changes.
