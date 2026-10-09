# Stage8 targeted owner contour approximation, signed source negative result (2026-10-09)

Input is frozen private two-case research candidate `PublicGeometryJS_RingStructuralAudit_20261009/neighbor_grid_round3`. Algorithm tries OpenCV approxPolyDP per ring for epsilons 0.25, 0.35, 0.45, 0.55, 0.7, 0.9, 1.2, 1.6 and accepts a change only when **every pixel in the full official OpenCV Stage8 owner raster is unchanged**.

## Findings

| Source case | Original signed Stage8 vertices | Candidate before | Candidate after | Additional savings | Original vertex cap |
|---|---:|---:|---:|---:|---:|
| GC001 | 3604 | 2156 | **2156** | **0** | 1887 (FAIL by 269) |
| Raden | 2370 | 1350 | **1350** | **0** | 1412 (candidate within cap by 62) |

Independent candidate comparison against original signed Stage8 11 owners: **PASS both**. 0 raw owner-mask pixel changes, same 8-connected component counts, RETR_TREE hole hierarchy and identity/owner/paint palette. This is an informative negative result, not a newly improved geometry. Do **not** relax masks/vertex caps or claim production success.

Remaining GC001 vertices by owner from the input candidate: `hair` 629, `__unbound__` 457, `major_clothing` 258, torso 170, head 151, neck 119. Plan alternate source-exact contour graph rerouting or a genuinely different topology-constrained optimization strategy; do not spend further cycles repeating this exact approxPolyDP grid.

This research tests OpenCV source-raster parity at 340x340 only. SVG DPR1/DPR4, 40-shape full-scene, original non-face RGB MAE, iPhone Safari and human Golden remain HOLD. No production switch, no source files modified. Private metrics and SHA-pinned candidate outputs stored in authorized Drive `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_TargetedOwner_20261009`.
