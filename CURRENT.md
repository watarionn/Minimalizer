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

Phase 5 is underway on `feature/rinka-target-phase5-macro-abstraction-20260908`. Checkpoint 1 adds conservative canonical outfit layer consolidation: at most one `character_outfit_detail` may merge into a `character_outfit_base`, only when color distance is <=24, detail area is <=18% of the base, spatial gap is <=1.8% of the short canvas side, left/right hints do not conflict, and the convex-hull result has >=0.94 IoU with the original two-shape union. On the fixed 16-image corpus this activates on exactly two images, Juufuutei Raden and Kikirara Vivi, removing one shape from each. Mean shape reduction improves from about **36.96% to 37.36%** and mean vertex reduction from about **30.09% to 30.29%**. Vivi preserves the rendered silhouette pixel-for-pixel; Raden changes only **4 silhouette pixels** (about **0.038%** of its target silhouette). The other 14 target PNGs remain byte-identical to Phase 4.

The user explicitly wants the completed Rinka Reference mode added to the Web UI. Keep it internal/opt-in while quality work is still moving; expose it in the Web UI only after the target style is judged complete and stable.

## Version rule

- `v0.3.0-alpha8 Character-specific Quality / Retry` is a historical checkpoint, not the current state.
- All alpha and rc builds are historical development checkpoints.
- Resume engine behavior work from **v0.3.0 stable** as the regression baseline.
- Keep Web runtime versions separate from the engine release line.
- The next engine development line should be `v0.3.x` for conservative fixes or `v0.4.0` for larger quality changes.

Read next: `HANDOFF.md`, then `docs/TARGET_STYLE.md` before quality work.
