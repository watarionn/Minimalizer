# Minimalizer Handoff

## Restore order

1. Read `CURRENT.md`.
2. Read this file.
3. Read `README.md` and `REPOSITORY_LAYOUT.md`.
4. Treat `v0.3.0 stable` as the engine regression baseline.
5. Inspect the restored code and tests before changing behavior.

## Current state

Minimalizer v0.3.0 stable is complete and is the engine regression baseline. The original product goal remains simple: input image -> minimalized graphic. Core minimalization quality takes priority over optional character-specific features.

GitHub contains the stable engine implementation, 39-file stable regression suite, all 16 original regression images, Web API/UI code, generic Docker packaging, and permanent CI.

Release validation recorded at v0.3.0:
- 156 tests passed / 0 failed when completed in batches.
- 16/16 corpus images processed successfully.
- mean corpus quality about 0.7893.
- mean identity about 0.9484.
- mean silhouette about 0.9114.
- 8192x6373 (52.21 MP) stress input completed successfully.
- `compileall` passed.

A single-process full pytest run exceeded the interactive execution window and is not counted as a completed pass.

## Web Phase

Web Phase 1 established the FastAPI adapter. Web Phase 2 added the browser workspace. Web Phase 3 added production safeguards and provider-neutral Docker packaging. Web Phase 4 is the first hosted-pilot phase.

Current Web behavior:
- `GET /` serves the browser UI.
- `GET /api/info` reports Web/engine versions and safety limits.
- `GET /health` provides a lightweight health check.
- `POST /api/minimalize` accepts one PNG/JPEG/WebP image and returns SVG or PNG.
- browser UI supports drag/drop, before/after preview, processing/error states, and SVG/PNG download.
- upload size, image side, and total pixel limits are enforced before engine processing.
- image-processing concurrency is bounded; excess overlapping work receives HTTP 429 with `Retry-After` rather than accumulating unbounded CPU jobs.
- basic security headers are returned and API/health responses use `Cache-Control: no-store`.
- the root `Dockerfile` runs as a non-root user and binds to the provider `PORT`.
- CI runs stable regressions, Web API/UI tests, and a real-Uvicorn WebP -> SVG smoke request.

Phase 4 hosted-pilot instrumentation adds:
- `X-Request-ID` on responses;
- `X-Minimalizer-Processing-Ms` on successful conversions;
- `Server-Timing` for total application request duration;
- privacy-conscious application logs containing request ID, validated format/dimensions, output format, processing time, and shape count, but not uploaded image contents or original filenames;
- environment-tunable Web limits, including `WEB_MAX_CONCURRENT_JOBS`.

Recommended first hosted settings:

```text
WEB_WORKERS=1
WEB_MAX_CONCURRENT_JOBS=2
```

See `docs/WEB_DEPLOYMENT.md` and `docs/WEB_PILOT_RUNBOOK.md`.

## Railway pilot

Railway is the preferred first hosted provider. Its current documentation says a root `Dockerfile` is automatically detected and GitHub repositories can be connected directly as service sources.

Do not add a new `railway.toml` or `railway.json` for this project. Railway Config as Code is deprecated and its legacy support is documented only through 2026-12-01. Use the root Dockerfile plus Railway service settings instead.

First deployment checklist:
1. connect `watarionn/Minimalizer` and deploy `main`;
2. keep `WEB_WORKERS=1` and `WEB_MAX_CONCURRENT_JOBS=2`;
3. set Railway healthcheck path `/health`;
4. enable public networking after a healthy deployment;
5. verify `/`, `/health`, `/api/info`, `/docs`, SVG, and PNG on the public URL;
6. record processing time and Railway peak memory for representative PNG/JPEG/WebP requests;
7. exercise the 429 busy path under overlapping requests;
8. tune limits only from observed measurements.

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

The immediate task is to perform the real Railway hosted pilot and write the measured results back into the deployment docs and handoff.

Engine maintenance remains queued in parallel:
1. audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of `0.985` and add a regression test if needed;
2. add a fully opaque RGBA high-resolution smoke test;
3. improve weaker corpus cases without regressing the stable baseline.

Prefer `v0.3.1` for safe engine fixes and `v0.4.0` for broader algorithm changes.
