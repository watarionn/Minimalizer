# MinimalizerPublic Stage8 independent signed owner replay matrix (2026-10-09)

Research-only continuation of PR #332. Signed original Stage8 11-owner geometry was compared against separately frozen source-visible owner masks for both GC001 and Raden.

Eight independent raster strategies were tested: native order, reverse order, depth-sorted order, reversed depth-sorted order, each with role-defined or parity-defined holes. This is not the official original Stage8 renderer. No source pixels, rings, holes, paint order, shape budget or production code were changed.

| Signed original | Exact with prior raster | Maximum exact with any tested 8-mode strategy | Owners still mismatching |
| --- | ---: | ---: | ---: |
| GC001 | 3/11 | 4/11 | 7 |
| Raden | 7/11 | 7/11 | 4 |

GC001 selected minimum pixel mismatches per owner include hair 250, lower body 105, right arm 45, neck 45 and structural head 24. Raden includes hair 147, left arm 74, neck 27, torso 18. These are per-owner mask pixel counts; do not sum them as a full-scene unique pixel difference. An individual owner's best strategy may conflict with z-order behavior, so mixing best modes is **not** proposed as production compositing.

Research runner: `tools/research/public_geometry_js/stage8_signed_owner_matrix.py`. It uses real 340x340 private binary owner masks with exact count checks, produces signed input SHA and a matrix of outside/missing pixels per owner/mode. Regression: 3/3 PASS on connected Windows Node/Python environment. The private signed per-role masks and original Stage8 JSON must remain in approved Drive, never public GitHub.

**Decision:** source Stage8 renderer reconstruction HOLD, no micro-ring deletion authorized, historical original source ring vertex caps GC001 3,604/1,887 and Raden 2,370/1,412 remain failed, full-face details disabled, Golden HOLD, production unchanged.

Next: inspect original Stage8 painter implementation for the precise treatment of degenerate 1-2-point contours, ring hierarchy, hole parity, layer overdraw and source mask compositing. Validate the exact original renderer across all 11 owners *before* deleting any source ring. Do not relax geometry budgets or claim a human Golden PASS.
