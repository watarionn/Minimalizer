# SA10.51: Signed source color within both expanded SVG vertex budgets

Date: 2026-10-09. **Research geometric-and-source-fidelity gate PASS on two signed cases; Stage8 source baseline, identity/visual Golden, and production still HOLD.**

## Goal and source fidelity

Reinvest SVG geometry cost reclaimed from compositor-occluded protected-trim rectangles into original-image-observed color boundaries inside the actual signed face guard, then into a few source-evidenced clothing/lower-body interiors. Never embed raster input images, invent absent anatomy, reuse a different character's z order, silently drop Stage9/37 apparel panels, or alter frozen champion SVGs or source masks. The legacy single-color Stage37 face reference is a stability baseline only, not the original-source fidelity target.

Two independent signed source image sets and their prior deployed-budget research champion SVGs are SHA-verified through SA10.50. Render through local Chromium 144.0.7559.96, 340×340 DPR1. Compare original-source **face-region RGB MAE** and original-source **visible character-region RGB MAE** separately from the flat-reference diagnostic. All reported counts are **expanded rendered mask paths + existing color polygons + every surviving trim rectangle (4 vertices each) + every new source color path occurrence**. A source RGB medoid is taken verbatim from a signed original pixel, never invented through image generation.

## Verified research measurements

| | Raden | GC001 |
|---|---:|---:|
| Frozen budget champion | 1,409 vertices | 1,883 vertices |
| Previous SA10.50 color experiment | 2,308 vertices | 2,746 vertices |
| **New SA10.51 color-preserving SVG** | **1,412 vertices** | **1,882 vertices** |
| Hard deployed geometry budget | **1,412** | **1,887** |
| Prior champion source face MAE | 50.752632 | 54.766660 |
| **New original-source face MAE** | **35.793353** | **29.404429** |
| Prior champion source visible-character MAE | 29.278547 | 47.924278 |
| **New original-source visible-character MAE** | **27.929286** | **44.728182** |
| Chromium full-scene zero-effect trims removed | **28 / 50** | **49 / 53** |
| Expanded vertices safely reclaimed | **112** | **196** |
| Duplicate signed face-mask reference occurrences added | **0** | **0** |
| Signed left and right arm final RGB changed versus champion | **0 / 0** | **0 / 0** |
| **Expanded budget and original-source face improvement** | **PASS** | **PASS** |

## Two source-grounded optimizations

1. **Complete-scene dead-correction proof:** the existing SA10.45/Raden or SA10.48/GC001 black protected-trim rectangles are individually removed in paint order. Every proposed deletion must render the entire 340×340 Chromium scene **bit-for-bit identically** to the previous signed champion. If a deletion changes even one final RGB pixel, it is reverted immediately. The final group of removals must likewise be bit-exact. The proof is source-scene and Chromium-version specific; do not generalize it to other characters or target renderers without rerunning. Saves Raden 112 and GC001 196 **real counted vertices**, not merely compressed SVG file bytes.
2. **Original face-mask reference elimination:** rather than an appended second masked face color group (SA10.50's 138 Raden/140 GC001 expanded mask reuse vertices), all observed face palette-region paths are inserted *inside* the already-existing signed final face guard after its base rectangle. Final face-mask reference remains **one**. Only source-observed LAB-cluster region polygons with true source-pixel RGB medoids are added, with every `M/L` vertex charged. Source face guard silhouette, signed role masks, owner paint/z order and Stage9/37 source color panels remain intact.

Policy selection tests strict-budget options for four palette clusters at `epsilon` 1.4, 1.8, 2, 2.5, 3, 4, 5, 6, 8, 10 and minimum connected-component areas 7 or 15. It renders feasible candidates in Chromium and minimizes **actual original-source face-region RGB MAE**, checking no pixels changed outside the signed face. Final selected epsilons: Raden **3.0/area 7**, GC001 **1.8/area 7**.

After face details, the optimizer tests *separate* original-source medoid color paths for existing `major_clothing`, `lower_body`, `torso`, and `hair` paint groups; each option is admitted only if it fits the remaining budget and improves both the source owner and whole visible-source MAE without changing signed face or either arm. Accepted: Raden major_clothing **9** new vertices, lower_body **3**; GC001 major_clothing **23** new vertices. The base owner may be recolored only with another actual source medoid and only when source MAE improves. No source-missing eye/nose/mouth path is invented.

## Actual artifact/test gates

- `tools/research/sa1051_budget_detail_optimizer.py` executes signed source authority checks, compositor-dead trim verification, real-Chromium face/detail budget search, source-only color selection and loss/budget/arm checks. Fails closed on missing source or tampered champion, extra masked face reference, unexpected SVG geometry or budget/fidelity regression.
- `tests/zerobase/test_sa1051_budget_detail_optimizer.py`: **9/9 PASS** against two private SHA-locked originals and champion SVGs, testing source/champion tamper, source pixel palette provenance, mask reuse accounting, source/output isolation, unapproved circle geometry, Chromium integration, face/source fidelity, final arm exactness and strict counted budget.
- A second full independent run produced **8/8 SHA-256 identical SVG, PNG and metrics/comparison artifacts**. Detailed per-owner candidate accounting, two frozen source identities, source MAE and digest ledger are in `sa1051_metrics.json`.
- Store comparison image (contains signed originals) and actual character SVG geometry **only** under approved private Drive path `chatGPT及びCodex用/Minimalizer/SA1051_BudgetedSourceColorDetail_20261009`. Commit GitHub code, tests, report and **coordinate-free** numerical metrics only. Do not push source photos, private SVGs or combined original-image comparison to public GitHub. No RDC, production worker or live site changed.

## What remains blocked

The under-budget SVGs now retain some original-observed face colors, but visual inspection still shows **coarse/fragmented eye shapes**, missing fine nose/mouth/hair and garment texture, and simplified silhouette details. Source pixel color paths are not an anatomical detector and do **not** certify recognizable source identity. Existing original Stage8 source ring budgets (Raden 2,370 vs 1,412; GC001 3,604 vs 1,887) still **FAIL** independently of deployed research SVG count. Human inspection and true multi-character Golden remain **PENDING/HOLD**, and no production or local worker promotion is authorized.

Next SA10.52: optimize source-observed eye/face connected feature geometry and clothing color plane boundaries under the genuine two-character budgets; develop shape-specific eye/nose/mouth landmark measurements sourced from the original 2D rather than hallucinating missing details. Protect signed silhouette and arm RGB and rerun entire mask/trim non-effect proofs. Evaluate original RGB and human visual quality, not merely flat-color equality. Production only after independently resolved Golden, source Stage8 policy, and human approval.

## Reproduction

```bash
python tools/research/sa1051_budget_detail_optimizer.py \
  --raden /signed/Raden --gc001 /signed/GC001 \
  --raden-svg /signed/SA1045/visible_guarded_budget.svg \
  --gc001-svg /signed/SA1048/gc001_guardless_component_budget.svg \
  --out /tmp/sa1051
SA1051_RADEN_ROOT=/signed/Raden SA1051_GC001_ROOT=/signed/GC001 \
  SA1051_RADEN_CHAMPION=/signed/SA1045/visible_guarded_budget.svg \
  SA1051_GC001_CHAMPION=/signed/SA1048/gc001_guardless_component_budget.svg \
  python -m pytest -q tests/zerobase/test_sa1051_budget_detail_optimizer.py
```
