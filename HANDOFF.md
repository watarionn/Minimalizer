# Minimalizer Handoff

## Restore order

1. Read `CURRENT.md`.
2. Read this file.
3. Read `README.md` and `REPOSITORY_LAYOUT.md`.
4. Treat `v0.3.0 stable` as the engine regression baseline.
5. Read `docs/TARGET_STYLE.md` before changing minimalization quality behavior.
6. Inspect the restored code and tests before changing behavior.

## Current state

Minimalizer v0.3.0 stable is complete and is the engine regression baseline. The original product goal remains simple: input image -> minimalized graphic. Core minimalization quality takes priority over optional character-specific features.

GitHub contains the stable engine implementation, 42-file regression suite, all 16 original regression images, Web API/UI code, generic Docker packaging, permanent CI, and a formal quality target specification in `docs/TARGET_STYLE.md`.

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

Web Phase 1 established the FastAPI adapter. Web Phase 2 added the browser workspace. Web Phase 3 added production safeguards and provider-neutral Docker packaging. Web Phase 4 completed the first real hosted pilot on Railway. Web v0.4.1 then fixed the production loading-state bug and added a hosted analysis-side safety cap for low abstraction levels.

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
- Web v0.4.1 obeys HTML `hidden` state globally so the processing overlay disappears after completion.
- Web v0.4.1 supports `WEB_MAX_ANALYSIS_SIDE` to cap hosted analysis resolution without changing desktop/CLI engine behavior.

Phase 4 hosted-pilot instrumentation adds:
- `X-Request-ID` on responses;
- `X-Minimalizer-Processing-Ms` on successful conversions;
- `Server-Timing` for total application request duration;
- privacy-conscious application logs containing request ID, validated format/dimensions, output format, processing time, and shape count, but not uploaded image contents or original filenames;
- environment-tunable Web limits, including `WEB_MAX_CONCURRENT_JOBS`.

Recommended hosted settings after the first pilot and v0.4.1 production follow-up:

```text
WEB_WORKERS=1
WEB_MAX_CONCURRENT_JOBS=2
WEB_BIND_PORT=8080  # Railway production service
WEB_MAX_ANALYSIS_SIDE=400  # temporary 1 GB hosted safety setting
```

See `docs/WEB_DEPLOYMENT.md` and `docs/WEB_PILOT_RUNBOOK.md`.

## Railway pilot

The first Railway hosted pilot was completed on the PR #5 branch `feature/web-phase4-hosted-pilot-20260908`.

Public production URL:
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

Representative Night River result on the final Phase 4 tested code commit `3a1a0f5dc8b4fc6b58e35a53204791c96577f63b`:
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

3. **Final Phase 4 code deployment verification**
   - Railway deployment `98f9e487-3905-47d1-a5e4-4a115427aff7` for commit `3a1a0f5dc8b4fc6b58e35a53204791c96577f63b` completed with `SUCCESS`.
   - Runtime log confirmed `Uvicorn running on http://0.0.0.0:8080` and `/health` 200.
   - The representative Night River request against that deployed code returned HTTP 200 with 31 shapes.
   - GitHub Actions CI run #17 for that code commit completed successfully.

4. **Low abstraction levels could exhaust the 1 GB host**
   - Production testing showed that levels 1-3 can be much heavier than level 4 because stable presets raise analysis size and preserve more palette/shape detail.
   - The public service recorded 502 responses and container restarts on low-level requests before the v0.4.1 hosted cap was added.
   - A temporary PR #6 Railway service showed that a level-1 representative request could still be killed with a 640 analysis cap.
   - At a 480 cap the same representative request completed with HTTP 200 but took about 108 seconds and used substantial memory.
   - At a 400 cap it completed with HTTP 200 in about 54 seconds and the service remained healthy.
   - These are hosted capacity observations, not engine-quality benchmarks or guaranteed timings.
   - Production therefore currently uses `WEB_MAX_ANALYSIS_SIDE=400` while further low-level performance tuning remains optional future work.

5. **Processing overlay remained visible after successful completion**
   - JavaScript correctly restored `hidden=true`, but author CSS `display` rules overrode the HTML hidden state.
   - Web v0.4.1 adds `[hidden] { display: none !important; }`.
   - User verification on the public production URL confirmed that the processing overlay now disappears and the minimalized result image is shown normally.

## Web v0.4.1 production verification

PR #6 `fix: stabilize low Web levels and loading state` was merged to `main` as commit:

`e7b20f51325cd4f3a2537e1e249b39312360b754`

GitHub Actions run #22 on that merged `main` commit completed successfully.

Railway production was corrected to track `main` rather than the older Phase 4 feature branch. Railway deployment `3a0da39d-20d9-4d04-bec8-a9b68c5f7fa9` deployed the merged v0.4.1 commit successfully and the production environment reported online with no active critical issues.

The current production safety setting is:

```text
WEB_MAX_ANALYSIS_SIDE=400
```

After that production deployment, the user manually verified the real public browser flow and confirmed:

- processing/loading UI disappears when minimalization finishes;
- the completed minimalized image is displayed;
- minimalization levels 1, 2, and 3 all complete successfully on the public production URL.

This is the current Web usability baseline. The earlier reported 502/loading-state failures are not reproducing in that verified production flow. Do not interpret this as a performance guarantee; low-level requests can still be computationally expensive on the 1 GB host.

Do not add a new `railway.toml` or `railway.json` for this project. Use the root Dockerfile plus Railway service settings instead.

## Formal quality target: Rinka Reference / 凛夏手本版

The user formally approved a hand-crafted ultra-minimal geometric poster variation as the target direction for future Minimalizer quality improvements.

The canonical visual reference is stored in Google Drive:

- folder: `chatGPT及びCodex用`
- file: `Minimalizer_目標スタイル_超ミニマル幾何学版_20260908.png`
- Drive file ID: `1muN6Lf5IHL8N64i57GAti255xu0sp0xY`
- URL: `https://drive.google.com/file/d/1muN6Lf5IHL8N64i57GAti255xu0sp0xY/view?usp=drivesdk`

Read `docs/TARGET_STYLE.md` for the full specification.

The essential direction is:

- preserve source identity through macro composition, silhouette, pose, dominant color blocks, and a few distinctive structural cues;
- prefer straight-edged polygons and angular planes;
- face details are optional and OFF by default for this target style;
- simplify hands into a few gesture-preserving blocks rather than detailed fingers;
- consolidate clothing into large masses and remove most ruffles, folds, trim, and micro-accessories;
- simplify the background more aggressively than the main subject, retaining only semantic scene cues;
- aggressively remove thin slivers, narrow rectangles, isolated micro-shapes, and repeated low-value fragments;
- prefer a compact role-based palette;
- prioritize intentional shape hierarchy and negative space over local contour fidelity.

The implementation goal is **input image -> intentional geometric poster**, not merely input image -> fewer contours.

This reference is a general design target, not an image-specific reproduction target. Do not add special cases for the reference image. Any engine change inspired by it must generalize across the stable corpus and future inputs.

## Rinka Reference implementation status

Phase 3 was merged in PR #9 as `5c0e17ac99d980d7f5d78ea7354a03058b7ee30a`. It added the opt-in target-style profile, large-shape hierarchy, identity-safe palette/epsilon choices, and conservative opaque subject/background inference. The public Web service is running that source, but normal Web requests still use the stable path.

Phase 4 is being developed on `feature/rinka-target-phase4-zones-20260908`. Its first foundation:
- derives coarse `head`, `torso`, `legs`, `left_arm`, and `right_arm` zones only after Phase 3 accepts an opaque subject;
- refuses zone inference for weak/non-vertical masks and falls back to Phase 3 behavior;
- tags overlapping shapes with zone-aware foreground roles and importance floors;
- uses a head-zone fallback for faceless micro-fragment suppression when explicit face metadata is unavailable;
- relaxes low-value head/arm/clothing/leg fragments conservatively before normal cleanup;
- records zone activation, confidence, bboxes, and per-zone shape counts in `target_style.opaque_zones`;
- extends corpus evaluation and CI safety guards for Phase 4;
- derives a conservative face-side color reference only from bilateral arm/head agreement or same-color head consensus;
- prefers dark-vs-face contrast for `hair`, but if that cue is absent it can use one geometry-gated color-contrast candidate that extends above and overlaps the face carrier, covering light-hair cases without fixed color tables;
- seeds `clothing` from the dominant color-separated torso/leg mass and propagates that identity only to nearby, similarly colored non-skin pieces;
- routes opaque arm-zone blocks through the hand/limb consolidation path with left/right `side_hint` preservation, preventing opposite sides from merging.

The next Phase 4 refinement adds light-hair geometry fallback, conservative clothing-mass propagation, and side-aware arm/hand consolidation. The new capability tests pass 21/21. A refreshed 16-image corpus run keeps the same 36.61% mean shape reduction, 29.94% mean vertex reduction, worst identity delta about -0.0573, and worst silhouette delta about -0.0010. The two currently activated corpus outputs are byte-identical PNGs to the prior Phase 4 HEAD, confirming that the generalized fallback paths do not alter existing accepted cases when their extra gates are not needed.

The user wants Rinka Reference added to the Web UI after the style is complete. Do not wire this moving target into the public UI prematurely; complete and stabilize quality work first, then add an explicit Web UI mode while preserving the normal stable mode.

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

Web v0.4.1 is merged and production-verified. The browser workflow is usable at levels 1-3 with the temporary hosted analysis cap of 400. Keep the current Railway safety settings while gathering more real usage evidence.

Primary product work should now shift back toward the original goal: input image -> higher-quality minimalized graphic, using `docs/TARGET_STYLE.md` as the formal visual direction.

Recommended quality sequence:
1. audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of `0.985` and add a regression test if needed;
2. add a fully opaque RGBA high-resolution smoke test;
3. strengthen generalized removal of visually low-value thin rectangles, slivers, and micro-fragments;
4. improve macro-shape selection so composition/silhouette outrank local contour detail;
5. explore gesture-preserving hand abstraction and garment-mass consolidation;
6. simplify background structure more aggressively than subject structure;
7. prefer straight-line polygonal geometry where source identity is preserved;
8. improve weaker corpus cases without regressing the stable baseline, especially identity/silhouette outliers;
9. keep safe maintenance fixes in `v0.3.1`, while larger target-style quality changes belong in `v0.4.0` or later.

Optional Web follow-up, after or alongside quality work:
- profile low-level retry/quality-evaluation cost on the 1 GB host;
- reduce level-1/2/3 processing time without degrading the intended detail presets;
- revisit `WEB_MAX_ANALYSIS_SIDE=400` only after new hosted measurements support a change.
