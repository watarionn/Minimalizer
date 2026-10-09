# SA10.47: Cross-character visible-owned SVG optimization, signed zero-face/arms gate

Date: 2026-10-09. **Research complete, production and full-character Golden HOLD.** This is a source-locked analysis, not a general character generation or design-quality certification.

## Goal and constraints

Generalize the SA10.45 visible-owner pruning and signed protection logic from Juufuutei Raden to GC001 without importing a character-specific part index, clothing emptiness assumption, source-owner/signed-arm alias, or modifying original Stage04/08/09/37/41 images. Build only geometric SVG from the SHA-validated source masks; no img2img, generative fill, embedded source PNG, synthetic facial feature, or official 3D. Strictly count SVG mask paths, all correction rectangles (4 vertices each), and all existing source Stage9 and Stage37 color polygons. **The historical Stage8 contour budget remains a separate failure.**

## Implemented

`tools/research/sa1047_two_case_visible_optimizer.py`: read both signed source sets via original SA10.43 and SA10.46 hash validators; derive actual owner z-order from each original source; preserve 11 source owner records, render-only owner/face masks and original Stage9/37 colored polygons. Compute source-visible regions by subtracting all later opaque source owners and the final signed face. Prove the exact pruned scene renders pixel-for-pixel identically to the fully exact source geometry **in Chromium 144.0.7559.96** before using it. Remove face underpaint and unpainted structural masks only if the signed scene structurally proves they are no-ops. GC001's four protected-clear overlay groups, including the five real garment panels, remain intact. Raden's historically proved empty-apparel group and unneeded clear mask may be pruned independently.

For nonprotected source owners, construct pixel-edge SVG polygons with several validated simplification distances, screenshot each isolated mask in real Chromium, detect new foreign paint in signed face and left/right arm masks, and insert black source-derived correction rectangles. Count all correction vertices. Optimize the finite candidates by a strict **per-character** multiple-choice budget DP. If none fits, report infeasibility for the tested choices and render a diagnostic low-complexity candidate; never silently lower the source budget or claim Golden. Finally rerender complete SVG through Chrome and measure signed final face/arms RGB and full-image mismatches separately. Group errors by the geometrically topmost *source owner*, **not** real-world material identity.

## Reproduced real Chromium measurements (340×340, DPR1)

| Metric | Raden | GC001 |
|---|---:|---:|
| Stage8 source ring vertices (historical) | 2,370 | 3,604 |
| Hard owner geometry budget | 1,412 | 1,887 |
| Exact pixel boundary, before source-visible pruning | 4,086 (SA10.44) | 6,083 (SA10.46) |
| New source-visible exact scene, expanded deployed vertices | **2,994** | **5,327** |
| Exact source-visible whole RGB mismatch vs signed OpenCV | **148 px** | **683 px** |
| New crosscase budget/diagnostic candidate, expanded deployed vertices | **1,411** | **2,925** |
| Budget candidate whole RGB mismatch | **884 px** | **1,980 px** |
| Budget candidate final signed face / left arm / right arm | **0 / 0 / 0 px** | **0 / 0 / 0 px** |
| New candidate expanded budget gate | PASS | **FAIL by 1,038** |
| Historical Stage8 source ring gate | FAIL | FAIL |

The GC001 optimizer preserves 5 garment overlay panels with 27 vertices, plus the Stage9 colors with 28 vertices. The fixed signed mask geometry plus overlays leaves only **548 vertices** for nonprotected hair/clothing/other owner masks. None of the measured per-owner candidates at epsilon {0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5} can satisfy that residual budget. This **does not** prove no other SVG representation is possible. Raden fits the strict deployed SVG budget with all three protected RGB regions exact, but this generalized candidate at 1,411 vertices/884 px is marginally worse than the **previous SA10.45 champion of 1,409 vertices/882 px**. Preserve the older champion and do not promote a regression.

GC001 remaining 1,980 pixel errors in the chosen minimum-complexity diagnostic are partitioned by topmost geometric owner: hair 567, lower_body 509, torso 220, major_clothing 203, unknown 162, neck 82, accessory 24, background 213. Protected face and both arms have 0. This is not evidence that those RGB differences correspond directly to semantic garment errors. The full-image comparison shows noticeable remaining hair/clothing interior error. No human reviewer approved the final visual quality.

## Tests, provenance and outputs

- `tests/zerobase/test_sa1047_two_case_visible_optimizer.py`: **8/8 tests PASS locally with both SHA-locked original source sets**, including source tampering rejection, disjoint lineage, apparel retention, protected arm owner differences, budget math, counted rectangle safety, forbidden mask geometry, real two-character Chrome integration, and output/input isolation. Tests skip private-source dependent work when source files are absent.
- Two independent full Chromium research evaluations generated **9/9 identical SVG/PNG artifact SHA-256 hashes**. The updated metrics include a deterministic owner-attribution ledger; full SHA-256 inventory and Chrome version in `sa1047_metrics.json`.
- Private source inputs remain only in approved Google Drive, **not committed to GitHub or embedded in any SVG**. Final PNG/SVG and report are archived in `chatGPT及びCodex用/Minimalizer/SA1047_TwoCaseVisibleOptimizer_20261009`.
- All product/worker/local/public endpoints unchanged, no automatic Golden promotion.

## Gate

`TWO_CHARACTER_SIGNED_EXACT_VISIBLE_RGB_REPLAY_PASS`; `TWO_CHARACTER_FINAL_FACE_ARMS_ZERO_RGB_PASS`; `RADEN_DEPLOYED_SVG_BUDGET_PASS` (but worse than champion); `GC001_DEPLOYED_SVG_BUDGET_FAIL`; `BOTH_HISTORICAL_SOURCE_VERTEX_BUDGET_FAIL`; `GLOBAL_RGB_GOLDEN_FAIL`; `HUMAN_VISUAL_REVIEW_PENDING`; `PRODUCTION_HOLD`.

## Next research, SA10.48

Prioritize **GC001 budget residual 548 vs mask requirements** without sacrificing the source-defined hair and clothing interior color plane ordering. Investigate structure-aware guard representation, safe mask reuse or owner-level source-visible arrangement where *expanded* complexity still counts all rendered geometry. Preserve the SA10.45 Raden champion. Only if two-character strict geometry budgets, signed protection, silhouette, full-scene RGB quality, and human visual inspection all pass may release gating be reconsidered.

## Reproduce (private source required)

```bash
python tools/research/sa1047_two_case_visible_optimizer.py --raden /path/to/signed_raden --gc001 /path/to/signed_gc001 --out /path/to/new_output --chromium /usr/bin/chromium
SA1047_RADEN_ROOT=/path/to/signed_raden SA1047_GC001_ROOT=/path/to/signed_gc001 python -m pytest -q tests/zerobase/test_sa1047_two_case_visible_optimizer.py
```
