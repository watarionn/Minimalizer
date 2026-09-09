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

The Character Structure bridge now extends Phase 4 subject-zone coverage beyond opaque scenes. On the fixed 16-image corpus, opaque zones remain 2/16 while Character Structure safely activates zones on all 11 subject-mode images, for 13/16 total subject-zone coverage and 193 classified shapes. Structure zones are advisory: existing canonical `character_*` shapes are left untouched, low-confidence body parts are dropped, background-like generic shapes are not spatially reclassified, and only generic subject fragments receive temporary zone-candidate semantics. The final corpus metrics remain exactly 36.61% mean shape reduction, 29.94% mean vertex reduction, worst identity delta about -0.0573, and worst silhouette delta about -0.0010. All 11 subject-mode target PNGs are byte-identical to Phase 4 HEAD `5faeb450a6434f982295ad0424678972dd8d87ce`, confirming the bridge adds future part-aware capability without perturbing accepted outputs.

The Phase 4 visual-review checkpoint then audited the surviving Structure candidates individually. Face/head candidates are retained because they touch identity-bearing regions. Two Mizumiya clothing accents are the only approved extra removals: each is a small, low-importance `target_zone_clothing_candidate` covered by at least 82% of a canonical garment mass. The rule is Structure-only and clothing-only. It removes exactly 2 shapes on the fixed corpus, changing Mizumiya from 23 to 21 shapes and 233 to 225 vertices while preserving the rendered silhouette pixel-for-pixel. The other 15 target PNGs remain byte-identical. Corpus means improve to about 36.96% shape reduction and 30.09% vertex reduction.

Phase 4 closure review is complete. The branch is clean against the unchanged Phase 3 `main` head, `git diff --check` passes, the latest fixed-corpus metrics reproduce the approved 36.96% shape / 30.09% vertex reductions with identity/silhouette safety intact, and no further generally safe reduction class was found in the 13 zone-enabled outputs. A repository-wide pytest run passes **193 tests** after deselecting exactly two legacy tests that reference the absent `tests/assets/false_face_phase85.png`; the fixture is missing on `main` as well and those tests are untouched by PR #10. Phase 4 was merged in PR #10 as `4ffcedc9f413a39d911e95cdc2b3c6573ed41a25` after explicit user approval.

Phase 5 starts from that merged Phase 4 baseline on `feature/rinka-target-phase5-macro-abstraction-20260908`. Its first checkpoint introduces conservative cross-layer garment mass consolidation for canonical outfit shapes only. A base can absorb at most one detail, with strict color/area/gap/side gates plus >=0.94 raster union-to-hull IoU. The fixed corpus activates exactly two merges (Raden and Vivi), improving mean shape reduction to about **37.36%** and mean vertex reduction to about **30.29%**. Vivi has zero silhouette-pixel change versus Phase 4; Raden changes four pixels (~0.038%). No other corpus target output changes. This is the first Phase 5 step toward garment-mass consolidation before broader gesture/macro-shape work.

Phase 5 checkpoint 2 introduces conservative gesture-preserving arm abstraction. Hands remain exact and act as same-side anchors; only arm polygons are candidates. Canonical arms require >=0.950 local raster IoU and opaque arms >=0.955, with <=8 degree major-axis drift, <=~1% short-side centroid motion, and a hand-connection guard. The fixed corpus simplifies exactly **4 arm shapes / 8 vertices**, improving mean vertex reduction to about **30.48%** while mean shape reduction stays about **37.36%**. Ririka changes one silhouette pixel, Subaru 21 (~0.074%), Todoroki zero, and Isaki is render-identical despite fewer vertices. The remaining 12 images are byte-identical to checkpoint 1. Keep hands untouched until a separately justified hand abstraction class passes visual review.

Phase 5 checkpoint 3 formalizes macro-shape priority as a ranking/telemetry layer before any tighter live shape budget. An experimental 24-shape level-4 post cap was tested and immediately rejected because Kanade's lowest-ranked nominal background shape is visually active near the head. The production target path therefore keeps the existing 28-shape budget. A shadow 24-shape audit now records what would be removed and blocks the proposal when a candidate overlaps the accepted subject bbox. On the fixed corpus the shadow proposal appears only on Kanade: **1 nominal-background candidate, 1 inside-subject-bbox candidate, blocked=true**. No live shape is removed and all 16 PNGs are byte-identical to checkpoint 2. Keep macro ranking active for future inputs, but do not tighten the live budget until shadow candidates are visually safe.

Phase 5 checkpoint 4 is the closure candidate. Shadow classification now includes a visual-subject-continuity guard based on subject-bbox overlap plus near-color/near-geometry continuity with definite subject shapes; Kanade's only 24-shape shadow candidate is therefore classified as subject-relevant rather than removable background. Keep live cap removal at zero. A second, stricter subject-mode-only outfit refinement pass adds exactly one additional Raden merge, bringing the fixed-corpus total to **3 outfit merges** and improving mean shape/vertex reduction to about **37.55% / 30.62%** while preserving the Phase 4/5 identity and silhouette safety lines. Hair has no further safe merge candidate. Compact/unknown hands were explicitly audited and rejected for simplification because no sample met the required geometry fidelity; hands remain exact anchors. The final 16-image visual review found no new regression. Phase 5 is ready for closure review rather than further threshold loosening.

Phase 5 was merged to `main` in PR #11 at `53a16682244c8a372825dd3804d92de993c8a947`. Phase 6 final polish starts from that exact baseline on `feature/rinka-target-phase6-final-polish-20260909` and is now complete/closure-passed. Its render-inert occlusion cleanup is intentionally narrow: only fill-only generic midground `subject_mass` / `subject_organic` structure fragments, <=3% canvas area, importance <0.60, no character/zone/gesture protection, and >=99.9% covered by later opaque fills in final z-order may be removed. Reverse render-order evaluation prevents a removed fragment from being used to justify another removal. The fixed corpus removes exactly **2 shapes** (Koganei Niko and Nerissa Ravencroft) and all **16/16 Phase 6 PNGs are byte-identical** to merged Phase 5. Mean shape/vertex reduction improves to about **37.94% / 31.37%** with identity/silhouette metrics unchanged. Final thin-sliver audit found no additional safe general class; preserve remaining hair lines, prop handles, limbs, boats/bridges and other meaningful slender structures. Closure passed with 38 target tests, 75 CI-like stable+Web tests, 207 repository-wide passes plus the two known missing-fixture deselections, compileall, fixed-corpus evaluation, and GitHub CI safety guards. Treat this as the **engine freeze candidate** and avoid further threshold loosening without new evidence.

The user wants Rinka Reference added to the Web UI after the style is complete. Once Phase 6 is merged, proceed to an explicit Rinka Reference Web UI mode while preserving the normal stable mode and its API behavior.

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


Phase 6 is merged and frozen at `a5e76fc365ad608bde7506b9b0a7b21a5e8527cc`. Web v0.5.0 integration starts from that exact baseline on `feature/rinka-web-ui-mode-20260909`. Add an explicit accessible segmented `?? / ?????` selector while keeping Standard selected by default. The API accepts `mode=standard|rinka_reference`; Standard preserves all existing controls, while Rinka Reference must stay locked to its validated Phase 6 level-4 profile and reject custom color/shape/background overrides. Both modes must obey the hosted analysis-size cap and processing semaphore. The response exposes `X-Minimalizer-Mode`; `/api/info` reports supported modes and `phase6`. Merge first, then verify both modes on the Railway production URL before calling v0.5.0 production-complete.


## Rinka Reference Phase 7 handoff

Phase 7 adds pre-cleanup Global Shape Scoring on `feature/rinka-global-shape-scoring-20260909`. The scorer combines existing macro priority, area, local importance, subject-zone overlap, semantic subject/background role, subject continuity, foreground placement, and a conservative sliver penalty. `cleanup_minimal_shapes()` now accepts optional global scores and a separate global-thin gate; its defaults leave Standard behavior unchanged.

Fixed-corpus evidence versus Phase 6: 3 additional global low-value slivers removed, mean shape reduction 37.94% -> 38.32%, mean vertex reduction 31.37% -> 31.58%, with identical pre-target identity/silhouette deltas. Global low-value audit: 101 total, 87 background, 0 subject, 11 thin candidates, exactly 3 removed. CI now records and guards these Phase 7 metrics.


## Rinka Reference Phase 8 handoff

Phase 8 is developed on `feature/rinka-phase8-subject-partition-20260909`. It is a narrow recovery path for the specific *failure class* where an opaque or nearly opaque character thumbnail remains in general-scene mode and collapses into two giant subject-colored polygons. The gate is geometric and corpus-backed, not filename-specific.

Activation requires strong border/background evidence, strong center foreground occupancy, a non-subject baseline result, largest filled shape >=25% canvas, and second-largest >=22%. The fixed corpus activates rescue exactly once. Other square character thumbnails such as Subaru, Raden and Noel remain on the normal Rinka path because they do not pass the two-giant-shape gate.

Accepted rescue inputs are converted to an inferred alpha subject, rerun through Character Structure, then rebuilt from real part masks using `minimalize_engine/character/rinka_macro.py`. The macro renderer retains a small number of face/hair/arm/lower-body/outfit masses and protected hand/prop detail. Do not broaden rescue activation without new corpus evidence.
Phase 8 fixed-corpus checkpoint at level 4 / analysis max side 220: mean shape reduction ~38.32%, mean vertex reduction ~32.22%, non-rescue worst identity delta ~-0.0449, non-rescue worst silhouette delta ~-0.0010. The rescue case reduces its largest final filled shape below 8% after the baseline gate records roughly 25.4% / 24.7% giant shapes. Local CI-equivalent suites pass 66 stable + 32 Web/Color Strip tests. Full pytest is 230 passed / 2 known missing-fixture failures (`tests/assets/false_face_phase85.png`).

Read `docs/RINKA_PHASE8_SUBJECT_PARTITION.md` before changing rescue thresholds, macro part budgets, or outfit color priority.
