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

Phase 3 is merged to `main` and production source, but the Rinka Reference path remains opt-in and is not exposed by the public Web UI.

Phase 4 work is underway on `feature/rinka-target-phase4-zones-20260908`. The foundation derives conservative coarse zones inside accepted opaque subjects and now also reuses existing Character Structure metadata for alpha/subject-mode scenes. Character Structure is treated as an advisory map: existing `character_*` base shapes keep their original role/layer/importance, low-confidence parts are ignored, and background-like generic shapes are not pulled into a person zone merely by spatial overlap. Generic subject fragments can receive temporary `target_zone_*_candidate` semantics so later cleanup knows whether they belong to head/hair/clothing/arms/legs without accidentally protecting them. The relative-color opaque path still supports dark-hair inference, geometry-gated light-hair fallback, conservative clothing propagation, and left/right arm side preservation.

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

The user explicitly wants the completed Rinka Reference mode added to the Web UI. Keep it internal/opt-in while quality work is still moving; expose it in the Web UI only after the target style is judged complete and stable.

## Version rule

- `v0.3.0-alpha8 Character-specific Quality / Retry` is a historical checkpoint, not the current state.
- All alpha and rc builds are historical development checkpoints.
- Resume engine behavior work from **v0.3.0 stable** as the regression baseline.
- Keep Web runtime versions separate from the engine release line.
- The next engine development line should be `v0.3.x` for conservative fixes or `v0.4.0` for larger quality changes.

Read next: `HANDOFF.md`, then `docs/TARGET_STYLE.md` before quality work.
