# MinimalizerPublic signed Stage8 structural + neighborhood grid campaign, 2026-10-09

Research-only follow-on from PR #338. **No original source scene was changed and no production deploy or merge is authorized.**

The canonical original Stage8 renderer was used with exact all-ring OpenCV even-odd 340×340 unguarded binary owner masks. Independent verification is against both frozen signed original scenes and all eleven owners, retaining owner/primitive IDs, palette, 8-connected topology and contour-hole hierarchy.

## Exact source raster results

| Research round | GC001 | Raden | GC001 cap gap | Raden cap margin |
| --- | ---: | ---: | ---: | ---: |
| Previous block replacement | 2,292 | 1,412 | +405 | 0 |
| Whole-ring source-exact removal | 2,284 | 1,409 | +397 | 3 below |
| Neighbor 1px point-fusion round 1 | 2,166 | 1,353 | +279 | 59 below |
| Neighbor 1px point-fusion round 2 | 2,156 | 1,351 | +269 | 61 below |
| Neighbor 1px point-fusion round 3 | **2,156** | **1,350** | **+269** | **62 below** |

Original frozen total source ring vertices: GC001 3,604 with strict historical cap 1,887; Raden 2,370 with cap 1,412. GC001 remaining source ring cap gap **269**, and identical greedy neighborhood grid search is at a local fixed point in the third round.

GC001 before these refinements is dominated by `hair` 676, `__unbound__` 471 and `major_clothing` 283 vertices. This does NOT imply those source-owned shapes can be dropped, especially 1px islands.

Scripts: `stage8_structural_inventory.py`, `stage8_whole_ring_probe.py`, `stage8_neighbor_grid_fusion.py`. Private signed input/candidate/evidence is kept under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_RingStructuralAudit_20261009/` with `neighbor_grid_round3/signed_original_parity.json`.

**Important:** A research ring-cap PASS for Raden, even with 62 vertex margin, is NOT whole-scene release qualification. Neither case has passed independently observed DPR4 browser SVG, source RGB full-character detail, 40-shape Golden, iPhone Safari or human Golden review. The original Stage8 signed source history must remain immutable. GC001's ring cap still FAILS.

Next technical investigation: explore source-exact contour rerouting/grouped perturbations beyond one-grid neighborhood, especially GC001 hair and unknown. Each candidate must preserve independent immutable raw per-owner source raster and topology and then pass browser DPR1/DPR4 before promotion.
