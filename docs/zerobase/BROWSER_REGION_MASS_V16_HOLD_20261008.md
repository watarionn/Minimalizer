# BrowserFallback Region Mass v16: negative result and next design gate

Date: 2026-10-08
Scope: browser fallback only, non-local, no Local Worker, no generative imagery.
Status: **HOLD_NO_COLOR_FIDELITY** (research branch only, NOT MERGED, NOT DEPLOYED).

## Hypothesis
After Facet v15, simplify regions themselves by reducing canonical hierarchy cut from 40 to 30 regions. Keep Lite structural mode (`l0-lite-jacobi`), canonical shared arcs and Facet polygon simplification. Experimental URL route is `?browserFallback=force&browserFallbackQuality=mass` **only in the isolated branch**, not publicly available.

## Controlled result: real Chrome 154 / Kyoko 340×340
Same input, same settings except hierarchyTargetMin=18 and hierarchyTargetMax=30 vs normal 24/40.

| Metric | Facet v15 | Mass v16 |
| --- | ---: | ---: |
| Region count | 40 | 30 |
| Rendered vertices | 1377 | 1072 |
| Minimum contour region IoU | 0.90206 | 0.90206 |
| Dominant green RGB | (149,211,27) | (178,211,72) |
| Dominant green pixels | 1994 | 4241 |
| Sleeve sample RGB (95,275) | (65,66,74) | (27,41,66) |
| Changed pixels vs Facet | - | 37.07% |

**Failure:** the green tie-associated mass expands again, and the left-sleeve gray becomes navy. Global contour IoU passes because it validates geometry *relative to each model's newly merged regions*, not fidelity to the reference assignment. Representative green count includes all pixels of that RGB across the output; it is not a manually annotated tie-only ROI. The fixed sleeve sample is similarly one point, but both align with the user's reported regression and 37% output-pixel change.

UI integration was tested in Chrome: the experimental Mass route and direct engine produced byte-identical PNG. This confirms the regression is caused by the region-cut strategy, not a routing error.

## Decision
- **REJECT / HOLD**: do not merge this experimental 30-region feature into main, do not deploy, and do not modify default Lite/Sharp/Shape/Facet/Exact modes.
- Shape count/vertex count **cannot** be the only objective.
- Add cross-mode source-aligned fidelity safeguards before attempting region merges: protected palette masses, high-contrast boundaries, important semantic-ish regions via observations *without reconstructing eyes/nose/mouth*, reference-color consistency, and explicit merge-level rollback. Preserve silhouettes and any thin distinctive color region including necktie.
- Only merge locally compatible, low-chroma-delta neighboring regions. Never globally lower hierarchy target before tests.

## Reproduction and preservation
The Chrome benchmark script lives on the development host (`_compare_browser_mass_v16.py`) and is preserved with images, metrics and source archive at [Google Drive Region Mass v16 HOLD](https://drive.google.com/drive/folders/1w_8szhjmGe5WnLhqwou7JaF7-o27darF), under the mandated `chatGPT及びCodex用/Minimalizer` hierarchy.

Future work: create a baseline-relative, candidate-by-candidate region merge gate. No production quality claim for Mass v16.
