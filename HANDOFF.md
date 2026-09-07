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

Web Phase 1 established the FastAPI adapter. Web Phase 2 added the browser workspace. Web Phase 3 added production safeguards and provider-neutral Docker packaging. Web Phase 4 completed the first real hosted pilot on Railway.

Current Web behavior:
- `GET /` serves the browser UI.
- `GET /api/info` reports Web/engine versions and safety limits.
- `GET /health` provides a lightweight health check.
- `POST /api/minimalize` accepts one PNG/JPEG/WebP image and returns SVG or PNG.
- browser UI supports drag/drop, before/after preview, processing/error states, and SVG/PNG download.
- upload size, image side, and total pixel limits are enforced before engine processing.
- image-processing concurrency is bounded; excess overlapping work receives HTTP 429 with `Retry-After` rather than accumulating unbounded CPU jobs.
- basic security headers are returned and API/health responses use `Cache-Control: no-store`.
- the root `Dockerfile` runs as a non-root user and supports an explicit `WEB_BIND_PORT` override before falling back to provider `PORT`.
- CI runs stable regressions, Web API/UI tests, and a real-Uvicorn default-level WebP -> SVG smoke request.

Phase 4 hosted-pilot instrumentation adds:
- `X-Request-ID` on responses;
- `X-Minimalizer-Processing-Ms` on successful conversions;
- `Server-Timing` for total application request duration;
- privacy-conscious application logs containing request ID, validated format/dimensions, output format, processing time, and shape count, but not uploaded image contents or original filenames;
- environment-tunable Web limits, including `WEB_MAX_CONCURRENT_JOBS`.

Recommended hosted settings after the first pilot:

```text
WEB_WORKERS=1
WEB_MAX_CONCURRENT_JOBS=2
WEB_BIND_PORT=8080  # Railway pilot service only
```

See `docs/WEB_DEPLOYMENT.md` and `docs/WEB_PILOT_RUNBOOK.md`.

## Railway pilot

The first Railway hosted pilot was completed on the PR #5 branch `feature/web-phase4-hosted-pilot-20260908`.

Public pilot URL:
- `https://minimalizer-web-production-a2bc.up.railway.app`

Verified endpoints:
- `GET /` -> 200.
- `GET /health` -> 200.
- `GET /api/info` -> 200.
- `GET /docs` -> 200.
- small PNG -> SVG -> 200.
- small PNG -> PNG -> 200.
- representative Night River WebP -> SVG -> 200.
- representative Night River WebP -> PNG -> 200.

Representative Night River result on the final tested code commit `3a1a0f5dc8b4fc6b58e35a53204791c96577f63b`:
- source: 1000x778 WebP;
- analysis size: 640x498;
- level: 4;
- output: SVG;
- HTTP 200;
- 31 shapes;
- engine processing time: 6143.0 ms;
- total application timing: 6203.4 ms;
- `X-Request-ID` present.

An earlier successful PNG output on the same OpenCV-4-compatible code path measured about 8288 ms, and SVG about 8045 ms. Treat these as pilot measurements, not performance guarantees.

Concurrency behavior was exercised on the public service. With `WEB_MAX_CONCURRENT_JOBS=2`, overlapping requests produced two successful 200 responses while the excess request returned HTTP 429 as designed. Keep this limit until additional capacity testing supports a change.

Railway metrics during the pilot on a 1 GB memory limit:
- observed memory maximum about 0.782 GB;
- observed post-test/current memory about 0.448 GB at the captured sample;
- observed CPU maximum about 0.357 vCPU in the captured one-hour window.

The 1 GB instance has useful but not generous memory headroom. Do not raise `WEB_WORKERS`, `WEB_MAX_CONCURRENT_JOBS`, the 64 MP pixel limit, or the current image-side limit without new measurements.

### Hosted-pilot issues found and fixed

1. **OpenCV 5 incompatibility**
   - Railway initially installed OpenCV 5.x from the unbounded dependency.
   - The normal level-4 path reached `cv2.HoughLinesP`, whose returned array shape differed from the stable engine assumption and caused `TypeError: 'numpy.int32' object is not iterable` in `minimalize_engine/geometry/lines.py`.
   - This was a dependency compatibility problem, not a WebP-format failure.
   - `opencv-python<5` and `opencv-python-headless<5` are now pinned.
   - CI now exercises `examples/input.webp` at level 4 so this exact path is covered.

2. **Railway bind-port mismatch during setup**
   - The generated public domain and injected/provider port state temporarily disagreed while the service was being configured.
   - `WEB_BIND_PORT` was added as an explicit container bind override for hosted environments that need it.
   - The final Railway pilot deployment bound Uvicorn to 8080, healthcheck `/health` returned 200, and the public domain targets the same service port.

3. **Final code deployment verification**
   - Railway deployment `98f9e487-3905-47d1-a5e4-4a115427aff7` for commit `3a1a0f5dc8b4fc6b58e35a53204791c96577f63b` completed with `SUCCESS`.
   - Runtime log confirmed `Uvicorn running on http://0.0.0.0:8080` and `/health` 200.
   - The representative Night River request against that deployed code returned HTTP 200 with 31 shapes.
   - GitHub Actions CI run #17 for that code commit completed successfully.

Do not add a new `railway.toml` or `railway.json` for this project. Use the root Dockerfile plus Railway service settings instead.

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

Web Phase 4 hosted-pilot validation is complete. PR #5 should remain unmerged until explicitly approved, but it is ready for final review once CI on the documentation-only handoff update is green.

After PR #5 is explicitly approved and merged, shift attention back toward the product's core goal: input image -> higher-quality minimalized graphic.

Engine maintenance / quality work remains queued:
1. audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of `0.985` and add a regression test if needed;
2. add a fully opaque RGBA high-resolution smoke test;
3. improve weaker corpus cases without regressing the stable baseline, especially identity/silhouette outliers;
4. keep safe maintenance fixes in `v0.3.1`, while larger quality changes belong in `v0.4.0` or later.
