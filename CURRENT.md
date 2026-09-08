# Minimalizer CURRENT

Current engine release: **v0.3.0 stable**
Current Web runtime: **v0.4.1 production-verified**

This file is the canonical restoration pointer.

## GitHub source of truth

The repository contains the restored **v0.3.0 stable implementation snapshot** itself, not only handoff metadata.

- Core source: `minimalize_engine/`, `app/`, `gui/`
- Web service: `web/`
- Regression tests: `tests/` with 42 `test_*.py` files
- Stable corpus: `tests/assets/corpus/` with 16 original images
- Corpus metadata: `tests/assets/corpus_manifest.json`
- Evaluation tools: `tools/`
- Stable sample input: `examples/input.webp`
- Formal quality target: `docs/TARGET_STYLE.md`

The restoration workflow verified that all 16 corpus entries exist, that 39 test files exist, that the restored Night River asset matches its original SHA-256, and that the Python source tree passes `compileall`.

## Current Web production state

Minimalizer Web is publicly hosted on Railway at:

`https://minimalizer-web-production-a2bc.up.railway.app`

Production currently tracks `main`.

Web v0.4.1 remains the public runtime. The current production source is `main` at merge commit `5c0e17ac99d980d7f5d78ea7354a03058b7ee30a`, which includes Rinka Reference Phase 3 as an opt-in engine path. Railway deployment `514a0040-9624-463b-a568-fa24c036b947` completed successfully for that commit.

Production uses the temporary hosted safety setting:

```text
WEB_MAX_ANALYSIS_SIDE=400
```

This setting is intentionally lower than the Web v0.4.1 code default because hosted testing showed that the 1 GB Railway runtime could still be killed on a representative level-1 request at an analysis cap of 640. A 400 cap is the current production safety setting while low-level performance tuning continues.

User verification on the public production URL confirmed:

- the processing overlay now disappears after minimalization finishes;
- the minimalized result image is displayed normally after completion;
- abstraction/minimalization levels 1, 2, and 3 all completed successfully on the public production service.

Treat this as the current hosted usability baseline. Further low-level performance optimization is still useful, but the previously reported production-blocking 502/loading-state issues are no longer reproducing in the user's verification flow.

## Formal quality target

The current visual quality target is **Rinka Reference / 凛夏手本版**.

Read `docs/TARGET_STYLE.md` before starting the next engine-quality phase.

The canonical reference image is stored in Google Drive under the user's `chatGPT及びCodex用` folder:

- file: `Minimalizer_目標スタイル_超ミニマル幾何学版_20260908.png`
- Drive file ID: `1muN6Lf5IHL8N64i57GAti255xu0sp0xY`
- URL: `https://drive.google.com/file/d/1muN6Lf5IHL8N64i57GAti255xu0sp0xY/view?usp=drivesdk`

The target direction is **intentional geometric poster**, not merely fewer contours. Preserve source identity through composition, silhouette, dominant color blocks, pose, and a small number of distinctive structures while aggressively simplifying face detail, hands, clothing micro-detail, background clutter, and low-value thin fragments. Straight-edged polygonal construction is preferred.

Do not add image-specific hacks to reproduce this one reference. Improvements must generalize across the stable corpus and future inputs.

## Rinka target development state

Phase 4 is merged to `main` in PR #10 as `4ffcedc9f413a39d911e95cdc2b3c6573ed41a25`. The Rinka Reference path remains opt-in and is not exposed by the public Web UI.

Phase 4 implementation and closure are complete and merged. Its foundation derives conservative coarse zones inside accepted opaque subjects and now also reuses existing Character Structure metadata for alpha/subject-mode scenes. Character Structure is treated as an advisory map: existing `character_*` base shapes keep their original role/layer/importance, low-confidence parts are ignored, and background-like generic shapes are not pulled into a person zone merely by spatial overlap. Generic subject fragments can receive temporary `target_zone_*_candidate` semantics so later cleanup knows whether they belong to head/hair/clothing/arms/legs without accidentally protecting them. The relative-color opaque path still supports dark-hair inference, geometry-gated light-hair fallback, conservative clothing propagation, and left/right arm side preservation.

Local 16-image Phase 4 evaluation at analysis max side 220 recorded:

- mean shape reduction: about **36.96%**;
- mean vertex reduction: about **30.09%**;
- worst pre-target identity delta: about **-0.0573**;
- worst pre-target silhouette delta: about **-0.0010**;
- opaque hierarchy enabled: **2 / 16**;
- opaque hierarchy / opaque zones enabled: **2 / 16**;
- Character Structure zones enabled: **11 / 16**;
- total subject-zone coverage: **13 / 16**;
- total subject-zone classified shapes: **193** (**173** from Character Structure + **20** from opaque zones);
- opaque refined shapes: head **3**, torso **7**, arm **4**, leg **4**, hair **1**, clothing **1**;
- face-side reference established on **1/16** images.
- the Structure bridge itself remains rendering-neutral across the 11 subject-mode cases;
- visual-review pruning now removes exactly **2** low-value clothing candidates on Mizumiya only when each is at least 82% covered by a canonical garment mass;
- Mizumiya changes from **23 -> 21 shapes** and **233 -> 225 vertices** with **0 silhouette pixels changed**; the other **15/16** target PNGs remain byte-identical to the pre-prune checkpoint.

Phase 4 closure review passed on 2026-09-08. `git diff --check` is clean, `main` is still `5c0e17ac99d980d7f5d78ea7354a03058b7ee30a`, and the Phase 4 branch is a direct descendant of that head. The full repository test suite passes **193 tests** when excluding exactly two pre-existing tests that both require the missing `tests/assets/false_face_phase85.png`; that fixture is also absent on `main`, and PR #10 does not modify either test. The latest 16-image closure evaluation reproduces **36.96%** mean shape reduction, **30.09%** mean vertex reduction, worst identity delta about **-0.0573**, worst silhouette delta about **-0.0010**, **13/16** total subject-zone coverage, **11/16** Character Structure coverage, and exactly **2** reviewed redundant-clothing removals. No additional safe Phase 4 reduction class emerged from the 13-image visual audit. Phase 4 was subsequently merged in PR #10.

Phase 5 is merged to `main` in PR #11 as `53a16682244c8a372825dd3804d92de993c8a947`. Checkpoint 1 adds conservative canonical outfit layer consolidation: at most one `character_outfit_detail` may merge into a `character_outfit_base`, only when color distance is <=24, detail area is <=18% of the base, spatial gap is <=1.8% of the short canvas side, left/right hints do not conflict, and the convex-hull result has >=0.94 IoU with the original two-shape union. On the fixed 16-image corpus this activates on exactly two images, Juufuutei Raden and Kikirara Vivi, removing one shape from each. Mean shape reduction improves from about **36.96% to 37.36%** and mean vertex reduction from about **30.09% to 30.29%**. Vivi preserves the rendered silhouette pixel-for-pixel; Raden changes only **4 silhouette pixels** (about **0.038%** of its target silhouette). The other 14 target PNGs remain byte-identical to Phase 4.

Phase 5 checkpoint 2 adds gesture-preserving arm abstraction while treating hands as fixed gesture anchors. Only arm polygons are simplified; hand polygons are never simplified by this pass. Canonical arms require local raster IoU >= **0.950**, opaque inferred arms require >= **0.955**, major-axis drift is capped at **8 degrees**, centroid movement is capped near **1%** of the short canvas side, and a same-side hand connection may not be worsened. On the fixed corpus this simplifies exactly **4 arms** and removes **8 vertices** with no shape-count change. One simplification is directly guarded by a same-side hand anchor. Mean vertex reduction improves from about **30.29% to 30.48%** while mean shape reduction stays **37.36%**. Versus checkpoint 1, Ririka changes **1 silhouette pixel**, Subaru **21 pixels (~0.074%)**, Todoroki **0 pixels**, and Isaki renders byte-identically despite its internal vertex reduction; the other 12 images are also byte-identical. Identity/silhouette safety metrics remain unchanged.

Phase 5 checkpoint 3 makes macro-shape priority explicit without tightening the live subject budget yet. The ranking now favors canvas area, canonical character bases, hair/garment masses, gesture carriers, semantic subject zones, and accepted opaque-subject shapes while penalizing true background. A trial level-4 post budget of 24 was rejected after visual review: it preserved numeric pre-target safety but would have removed a Kanade midground shape visibly contributing near the head. The live default therefore remains the upstream/final **28-shape** budget. A shadow 24-shape audit is now recorded instead. On the fixed corpus, only Kanade exceeds that shadow budget; exactly **1** candidate would be removed, it is nominally background but overlaps the overall subject bbox, and the shadow audit marks the proposal blocked. Actual output remains **16/16 byte-identical** to checkpoint 2 with **37.36%** mean shape reduction, **30.48%** mean vertex reduction, and zero live cap removals.

Phase 5 checkpoint 4 / closure candidate tightens the final quality audit without forcing a lower live budget. Macro-shadow classification now recognizes **visual subject continuity**: a nominal background/midground shape inside the subject bbox is reclassified as subject-relevant when it is spatially close to a definite subject shape and has near-identical color. On the fixed corpus, Kanade's sole 24-shape shadow candidate is now correctly recorded as **subject continuity (1)** rather than safe background (0), so live cap removal remains **0**. A separately gated second garment pass, available only for subject-mode scenes with Character Structure, accepts one additional extremely safe Raden merge (union-to-hull IoU >=0.96, color distance <=16, detail/base area <=14%, gap <=1% short side). Corpus outfit merges therefore rise from 2 to **3**, mean shape reduction improves to about **37.55%**, and mean vertex reduction to about **30.62%**, with worst identity/silhouette deltas unchanged. Hair audit found no additional safe merge class. Compact/unknown-hand audit found no acceptable hand simplification (the only reducible sample fell to about 0.92 local IoU), so hands remain exact gesture anchors. Final 16-image visual review found no Phase 5 regression.

Phase 6 final polish is complete on `feature/rinka-target-phase6-final-polish-20260909` and has passed closure review. Its final cleanup class removes only render-inert generic midground `subject_mass` / `subject_organic` fills that have no stroke, are low-importance/non-canonical/non-zoned, and are >=99.9% covered by opaque fills that render later in the final z-order. Candidates are processed from the top of the stack downward, so a removed candidate can never act as the occluder for another removal. On the fixed 16-image corpus this removes exactly **2** shapes (Koganei Niko 1, Nerissa Ravencroft 1). All **16/16 target PNGs are byte-identical to the merged Phase 5 baseline**, while mean shape reduction improves from about **37.55% to 37.94%** and mean vertex reduction from about **30.62% to 31.37%**. Worst identity/silhouette deltas remain unchanged. A separate thin-sliver audit found no additional generally safe class: the remaining extreme-aspect shapes are meaningful hair lines, prop handles, limbs, boats/bridges, or other composition carriers, so Phase 6 does not broaden deletion thresholds. Closure checks passed with **38/38 target tests**, **75/75 CI-like stable+Web tests**, **207 passed / 2 deselected** repository-wide tests, compileall, fixed-corpus evaluation, and GitHub CI safety guards. Rinka Reference is now the engine-level **completion/freeze candidate**; do not add broader cleanup thresholds unless a new regression or corpus-backed need is demonstrated.

The user explicitly wants the completed Rinka Reference mode added to the Web UI. After Phase 6 is merged, the next product step is to expose it as an explicit Web UI mode while preserving the normal stable mode unchanged.

## Version rule

- `v0.3.0-alpha8 Character-specific Quality / Retry` is a historical checkpoint, not the current state.
- All alpha and rc builds are historical development checkpoints.
- Resume engine behavior work from **v0.3.0 stable** as the regression baseline.
- Keep Web runtime versions separate from the engine release line.
- The next engine development line should be `v0.3.x` for conservative fixes or `v0.4.0` for larger quality changes.

Read next: `HANDOFF.md`, then `docs/TARGET_STYLE.md` before quality work.
