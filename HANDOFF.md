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

Web Phase 1 established the FastAPI adapter without changing stable engine algorithms. Web Phase 2 adds the first browser workspace on top of that API.

Current Web behavior:
- `GET /` serves the browser UI.
- `GET /api/info` reports Web and engine version information.
- `GET /health` provides a lightweight health check.
- `POST /api/minimalize` accepts one uploaded image through multipart form data.
- output formats: SVG and PNG.
- basic overrides: abstraction level, palette colors, target max shapes, and background mode.
- upload size is capped at 20 MB on both client guidance and server enforcement.
- CPU-bound minimalization runs through a thread pool.
- browser UI supports drag-and-drop/file selection, source/result side-by-side preview, processing/error/empty states, SVG download, PNG download, and responsive mobile layout.
- secondary settings are collapsed by default so the core image -> minimalize workflow stays primary.
- Web server dependencies are isolated from PySide desktop GUI dependencies.
- CI covers both stable smoke regressions and Web integration tests.

Run locally with:

```bash
python -m pip install -r requirements-web.txt
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
```

See `web/README.md` for browser and API usage.

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

Web Phase 3 should focus on production-readiness before choosing a hosting provider:
1. strengthen upload validation and request/concurrency limits;
2. add end-to-end browser verification for the drag/drop -> preview -> download flow;
3. define deploy/runtime packaging and health/readiness behavior;
4. then evaluate production hosting based on CPU/image-processing needs and cost.

Engine maintenance remains queued in parallel:
1. audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of `0.985` and add a regression test if needed;
2. add a fully opaque RGBA high-resolution smoke test;
3. improve weaker corpus cases without regressing the stable baseline.

Prefer `v0.3.1` for safe engine fixes and `v0.4.0` for broader algorithm changes.
