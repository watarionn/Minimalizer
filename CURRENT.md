# Minimalizer CURRENT

Current engine release: **v0.3.0 stable**
Current production Web runtime: **v0.10.0 production-verified**
Current Rinka Reference engine: **Phase 12 merged and production-verified; Phase 13 color-anchor local closure complete** on `feature/rinka-phase13-face-hair-color-anchor-20260911`
Current Web runtime remains **v0.10.0**; the Phase 13 candidate changes only Rinka color-anchor behavior and reports Rinka Reference `phase13`.

This file is the canonical restoration pointer.

## Latest development: Rinka Reference Phase 13

Phase 13 improves source-color fidelity for the Phase 12 faceless face slab and major hair anchor. Face pixels are clustered and ranked for skin plausibility plus background separation instead of using one raw median. Hair pixels are clustered independently; bright low-chroma source clusters are preferred, and if the dominant hair candidate is too face-like, a better-separated real source cluster is selected. This specifically targets pale-skin / white-hair portraits on bright backgrounds without adding facial features or hair micro-detail. See `docs/RINKA_PHASE13_COLOR_ANCHOR.md`. Closure passes **269 tests / 2 known missing-fixture deselections**, dedicated Phase 12+13 **10/10**, the fixed 16-image evaluator with unchanged Phase 12 corpus metrics, `compileall`, Web JavaScript syntax, `git diff --check`, and real-Uvicorn HTTP 200 smoke for Standard, both Rinka presets, and Color Strip.

## Latest development: Rinka Reference Phase 12

Phase 12 adds a failure-gated Head / Body Anchor Guard for opaque portrait inputs that still collapse into two or three giant slabs after the normal Rinka path. Rejected AI-free subject masks are retained as candidates but remain inactive unless a dedicated portrait-collapse gate accepts them. Accepted repairs rebuild subject color planes, synthesize one faceless skin-colored face slab plus one large hair anchor, require at least one torso anchor, and then pass a repair-quality gate before replacement is allowed. If the repair misses its required anchors, subject coverage falls below 0.64, or outside-subject overdraw exceeds 0.04, the renderer falls back to the previous baseline result.

The two supplied regression images are now both handled by Phase 12: the white-hair case activates the three-slab route and the red-poster case activates the stricter two-slab-poster route. On the fixed 16-image corpus, Phase 12 rescue remains **0/16**, so established Phase 11 output metrics and poster-background behavior remain unchanged. Dedicated Phase 12 tests cover three-slab acceptance, two-slab poster acceptance, small-third-slab rejection, face anchor extraction, hair anchor extraction, and repair-quality requirements. See `docs/RINKA_PHASE12_HEAD_BODY_ANCHOR_GUARD.md`.

## Latest development: Rinka Reference Phase 11

Phase 11 adopts the reviewed faceless geometric poster examples as the target direction. Priorities 1 and 2 were merged in PR #22 at `c5691318df69e1030ca89dd6a404e58294ba24a1`: strict faceless cleanup, one fingerless hand symbol per side, stronger micro-detail removal, larger hair planes, and larger outfit color blocks. Stable/Standard behavior remains untouched.

Checkpoint 3 is merged and production-verified from that exact Phase 11 line. The default Rinka preset is `geometric_poster`: it keeps the accepted Phase 11 subject shapes unchanged and adds a flat poster background with three large five-vertex panels only when subject evidence exists. `faceless_subject` keeps the Phase 11 person abstraction but does not synthesize a background. A broad first background prototype was rejected during development because treating every generic `midground` shape as disposable could erase subject-supporting structure; the accepted gate only replaces definite background shapes. On the fixed 16-image corpus, geometric backgrounds activate on **15/16** character cases, generate/survive **45/45 panels**, and leave Night River untouched. The subject-shape signature is identical between the two presets on all **16/16** corpus images. The geometric preset currently measures about **31.10%** mean shape reduction and **21.59%** mean vertex reduction because its three intentional poster panels are counted as output geometry; Checkpoint 2 subject-only abstraction remains available unchanged through `faceless_subject`. Web v0.9.0 production adds a Rinka preset selector while Standard remains the default mode. See `docs/RINKA_PHASE11_GEOMETRIC_POSTER_ABSTRACTION.md`. Local closure passes **259 tests / 2 known missing-fixture deselections**, `compileall`, JavaScript syntax validation, `git diff --check`, real-Uvicorn smoke for all four Web paths, and final 16-image visual/evaluator review.

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

Web v0.10.0 is the public runtime. The current production source is `main` at merge commit `2da9b1aa693bbc68dde8a59994bff9503673f7d8`, which includes Rinka Reference Phase 12 Head / Body Anchor Guard. Railway deployment `940903ca-4afc-4558-b5bb-d78d78ad60b4` completed successfully for that commit; `/health`, `/api/info`, Standard, both Rinka presets, and Color Strip were verified with HTTP 200.

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


## Rinka Reference Phase 7: Global Shape Scoring

Phase 7 reopens the former Phase 6 freeze only for a corpus-backed improvement: global visual value now participates before cleanup so macro composition, subject continuity, semantic mass, foreground placement, and area can outweigh local contour importance.

The new global scoring path is opt-in from Rinka Reference only. Stable/Standard cleanup defaults remain unchanged. Low-value global sliver removal is gated by score, geometry, area, and existing semantic protection.

On the fixed 16-image corpus at level 4 / analysis max side 220, Phase 7 removes 3 additional low-value slivers versus Phase 6, improves mean shape reduction from about 37.94% to 38.32%, and mean vertex reduction from about 31.37% to 31.58%. Pre-target identity/silhouette metrics are unchanged versus the Phase 6 baseline. Global scoring classified 101 shapes as low-value, including 87 background shapes and 0 subject shapes; 11 were thin candidates and exactly 3 passed the deletion gate.


## Rinka Reference Phase 8: Subject Macro Partition

Phase 8 is in development on `feature/rinka-phase8-subject-partition-20260909`. It addresses a corpus-backed failure where an opaque character thumbnail can stay in general-scene mode and collapse into one or two giant color polygons.

The new path is failure-gated rather than generally enabled. A candidate image is first run through the normal Phase 7-compatible path; rescue activates only when the output is still non-subject, the background/center evidence is strong, and two giant filled shapes remain (largest >=25% canvas and second >=22%). On the fixed corpus this gate activates only for Omaru Polka; Raden, Subaru, Noel, Night River City and the other samples stay on the established path.

When activated, an inferred alpha mask is sent through Character Structure and real part masks are rebuilt as a compact semantic macro composition: face, hair, left/right arms, left/right lower body, outfit, plus protected hand/prop details. Outfit base-color ranking also considers perceptual distance from the face so accidental skin-colored overlap does not dominate a garment mass.
Current fixed-corpus evidence at level 4 / analysis max side 220:

- mean shape reduction: about **38.32%**;
- mean vertex reduction: about **32.22%**;
- rescue activated: **1 / 16**;
- macro partition activated: **1 / 16**;
- worst non-rescue identity delta: about **-0.0449**;
- worst non-rescue silhouette delta: about **-0.0010**;
- rescue-case largest final filled shape: below **8%** of canvas.

For Omaru, the normal-path failure gate sees giant filled-shape ratios of about **25.4% / 24.7%**, while the Phase 8 macro result suppresses the one-slab failure. Dedicated Omaru-rescue and Subaru-non-rescue tests are included. CI-like local suites pass 66 stable tests + 32 Web/Color Strip tests, and repository-wide pytest reports **230 passed / 2 failed**, where both failures are the pre-existing missing `tests/assets/false_face_phase85.png` fixture cases.


## Rinka Reference Phase 9: Semantic Primitive Optimization

Phase 9 is developed on `feature/rinka-phase9-semantic-primitives-20260909` from the merged Phase 8 baseline. It keeps the Phase 8 rescue activation gate unchanged and improves only the rescued semantic macro composition.

The rescue renderer now builds a Semantic Shape Tree, enforces per-part primitive budgets, and compares localized primitive candidates instead of always accepting a simplified contour polygon. Face may become an ellipse, outfit may become a compact trapezoid, and semantic boundaries remain explicit. A conservative head-feature pass can preserve a small distinctive high-contrast accessory cue.

On the fixed 16-image corpus at level 4 / analysis max side 220, Phase 9 records about **38.72%** mean shape reduction and **32.76%** mean vertex reduction. The semantic tree / primitive path activates on exactly **1/16** images. Non-rescue worst identity and silhouette deltas remain about **-0.0449 / -0.0010**. The rescue case ends with largest/second filled-shape ratios about **6.39% / 5.37%**, below the Phase 8 safety limits.

Current dedicated telemetry: Semantic Tree enabled **1**, primitive fits **9**, head feature enabled **1**, face ellipse **1**, outfit trapezoid **1**. Read `docs/RINKA_PHASE9_SEMANTIC_PRIMITIVES.md` before changing the primitive priors, semantic budgets, or head-feature gates.

## Phase 10 AI-free Subject Segmentation checkpoint 1 (2026-09-10)

Development resumed from current `main` on `feature/rinka-phase10-ai-free-subject-segmentation-20260910`. The first Phase 10 checkpoint adds deterministic subject/background segmentation for the opaque-character failure class. It uses border-color evidence plus edge-connected background components and does not use AI or learned models. The established Phase 8 giant-slab gate remains in front of the new path, so the fixed corpus changes only the known Omaru Polka rescue case.

Real-image iteration rejected a broad prototype set that treated white subject edges as background, rejected a trimmed-bbox experiment that damaged pose layout, and rejected direct reuse of the Phase 9 semantic-macro rescue with the new mask. The accepted path converts the failure-gated image into an alpha subject, uses ordinary Character Structure analysis, and removes the now-redundant giant `subject_base` only when Phase 10 segmentation is actually active. On Omaru, the largest final filled shape is about 15.7% of canvas instead of the rejected prototype's 50.8% slab.

Read `docs/RINKA_PHASE10_AI_FREE_SUBJECT_SEGMENTATION.md` before continuing. The next Phase 10 step is within-subject simplification that preserves the raised-arm gesture and major color blocks while moving the separated subject closer to the 凛夏 reference.

## Rinka Reference Phase 10 Checkpoint 2 (2026-09-10)

Checkpoint 2 is implemented locally on `feature/rinka-phase10-ai-free-subject-segmentation-20260910`. After the existing failure-gated AI-free segmentation accepts an opaque character thumbnail, the accepted path now rebuilds subject internals as a deterministic six-color polygon scaffold in `minimalize_engine/subject_planes.py`. Small same-color gaps are bridged only inside the accepted subject mask before contour simplification. Hand and prop/weapon carriers from Character Structure are retained on top of the scaffold, and a conservative dark side-plane detector protects the raised-arm gesture.

For Omaru at level 4 / analysis max side 220, the current scaffold has 24 subject planes / 126 scaffold vertices, one protected gesture plane, one backdrop-contrast color adjustment, about **76.99%** segmented-subject coverage and about **1.35%** outside-subject overdraw. Final output is 26 shapes / 137 vertices. Direct rendered foreground versus the accepted segmentation mask measures about **0.756 IoU / 0.764 recall**, compared with Checkpoint 1's **0.651 IoU / 0.661 recall** at 25 shapes / 187 vertices.

The fixed 16-image evaluator still activates Phase 10 segmentation/scaffolding on exactly **1/16** images. The other 15 retain worst pre-target identity/silhouette deltas around **-0.0449 / -0.0010**. Mean corpus shape/vertex reduction is about **36.71% / 31.38%**. Rejected trials include full silhouette underlays, local-color gap carriers, 5x5/7x7 color closing, and 0.05 contour epsilon because they produced oversized slabs or damaged pose structure.

Do not push this Checkpoint 2 work merely to run GitHub Actions while metered Actions usage could become chargeable. Finish and validate locally first. The open Draft PR remains #20 until a safe update path is available.

## Rinka Reference Phase 10 Checkpoint 3 (2026-09-10)

Checkpoint 3 is implemented on `feature/rinka-phase10-checkpoint3-fragment-consolidation-20260910` from merged Phase 10 Checkpoint 2. It adds deterministic small-fragment absorption, saturation/gesture protection, raster-IoU-guarded adaptive polygon simplification, macro-anchor prioritization, and a 17-plane scaffold cap. The Phase 10 activation gate now covers four opaque thumbnails without filename-specific rules: Polka via the original giant-slab gate, Subaru/Noel via high-confidence subject structure, and Raden via a dense-subject gate.

Fixed 16-image level-4 / 220px evidence: Phase 10 activation **4/16**, total subject planes **68**, total scaffold vertices **738**, total gesture planes **5**, mean subject-plane coverage about **75.90%**, maximum outside-subject overdraw about **2.45%**, and unaffected 12-image worst identity/silhouette deltas about **-0.0185 / -0.0010**. Mean corpus shape/vertex reduction is about **34.64% / 25.06%**. The lower reduction percentages are an intentional trade for substantially safer subject reconstruction on the newly activated thumbnails.

Local validation: dedicated Phase 10 **6/6**, combined Phase 8/9/10 + target-style + Web API **65/65**, repository-wide **241 passed / 2 deselected** (the same missing `false_face_phase85.png` fixture tests). GitHub Actions must remain skipped while metered usage may be chargeable; local validation is the evidence for this checkpoint.
