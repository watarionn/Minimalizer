# Source-signed Stage8 micro-ring single deletion, 2026-10-09

**Fail-closed actual deletion counterfactual conducted; authorized safe deletions = 0.**

Based on two frozen signed GC001/Raden Stage8 scenes, source-visible signed owner masks (each checked against private SHA manifest), and cv2 original pixel-grid fill/hole replay. Every ring remains untouched in source data; removal is a temporary independent render to compare with the original mask.

| Gate | GC001 | Raden |
| --- | ---: | ---: |
| Original Stage8 1-2 point micro-rings | 110 | 13 |
| Signed owners where baseline ring raster exactly matches independently signed owner mask | 3 of 11 | 7 of 11 |
| Micro-rings in exactly reproduced owners | 5 | 2 |
| Rings removable individually with zero source-owner pixel difference | **0** | **0** |
| Remaining candidates rejected or lacking valid baseline | 110 | 13 |

In all other owners, a simple sequential cv2 drawContours reconstruction differed from the independent original signed owner masks even **before any deletion**. Do not treat ring-removal comparisons there as proof of equivalence; extra fill/hole topology and compositing semantics require an exact original renderer. The successful baseline subset provides a conservative negative control: deleting any one of its seven micro-rings changes at least one signed source-owner pixel.

The source-pixel ownership trace separately verified 163 GC001 and 17 Raden micro-ring points are inside their own signed visible masks, with no later signed owner at those coordinates. That is sample evidence, **not** a pixel deletion approval.

Research code: `tools/research/public_geometry_js/stage8_micro_ring_delete_trial.py`, `stage8_micro_visibility_gate.py`; private SHA-signed evidence remains in user Drive only. **No Stage8 budget waiver, no source deletion, no production import, no face microfeatures, no Golden PASS.**

Next work: reproduce the full original Stage8 owner renderer bit-exactly (including degeneracies, hierarchy and source-mask fill semantics), confirm replay across all 11 owners, then run one-ring counterfactuals and original RGBA + DPR4 tests. Current Stage8 historical budgets remain GC001 3604>1887 and Raden 2370>1412.
