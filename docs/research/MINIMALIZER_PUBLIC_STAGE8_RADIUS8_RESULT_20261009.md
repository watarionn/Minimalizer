# Stage8 radius-8 signed original owner raster research (2026-10-09)

Research only, original signed SA10.34 GC001/Raden Stage8 scenes unchanged. This experiment expanded neighboring grid candidate points for 2-to-1 contour vertex fusion to ±8 px from the midpoint. Every acceptance required identical official one-pass OpenCV FILLED even-odd unguarded owner raster; a separate original-source comparison then verified all 11 original owners, 8-connected component counts, RETR_TREE hole hierarchy and owner/primitive/color identities.

| Case | Original signed ring count | Radius-7 baseline | Radius-8 candidate | Historical hard cap | Over cap |
|---|---:|---:|---:|---:|---:|
| GC001 | 3604 | 1946 | **1941** | 1887 | **54** |
| Raden | 2370 | 1182 | **1177** | 1412 | 0 |

Results from the independent source gate: GC001 removed 1663 total signed ring vertices with all 11 source owner rasters exact; Raden removed 1193 total and all 11 owners exact. The +5/+5 incremental improvement took an approximately 81-second Windows research run; diminishing returns suggest a different contour-graph method is warranted, rather than continuing blind radius escalation.

Private candidate scenes and source SHA/owner parity record are in `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_Radius8_20261009`. Source code `tools/research/public_geometry_js/stage8_neighbor_grid_radius8.py`. No original scenes, palettes, face output rules or production code were changed.

**GO/NO-GO**: Original 340×340 owner-mask research verification PASS. GC001 original hard ring cap FAIL by 54; Raden candidate vertex budget PASS only for the research representation. Browser SVG DPR1/DPR4 and original RGB quality, 40-shape whole character, iPhone Safari, human Golden review and production integration remain HOLD. No merge, deployment or cap waiver.
