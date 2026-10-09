# MinimalizerPublic Multi-point exact signed Stage8 contour research (2026-10-09)

**Research candidate PASS for original OpenCV raw pixel and topology. Historic vertex caps, browser SVG, human Golden and production remain HOLD.**

Building on draft #335's privately SHA-pinned 40,000-trial single-point Stage8 candidate, the new span deletion optimizer examines removals of 2 to 8 consecutive contour points and accepts an edit ONLY if the complete unguarded Stage8 raw 340×340 owner mask is byte-equivalent to its starting mask. This is NOT image generation, restoration, new face drawing or approximate raster fit. Retained original primitive IDs, part ownership, z-order, RGB palette and frozen source association are checked against the immutable SA10.34 original scenes in an independent gate.

| Research pass | GC001 final vertices | GC001 removed from 3,604 | Raden final vertices | Raden removed from 2,370 |
| --- | ---: | ---: | ---: | ---: |
| Single-point 40k | 2,864 | 740 | 1,786 | 584 |
| Multi-span 12k per owner | 2,610 | 994 | 1,561 | 809 |
| **Multi-span 30k per owner** | **2,562** | **1,042** | **1,507** | **863** |

**Independent frozen original-source revalidation PASS** for 30k:
- Both original input Stage8 source counts agree: GC001 3,604 and Raden 2,370.
- All 11 original owners have **0 changed pixels in the unguarded official canonical OpenCV filled contour raster** versus the independently loaded research candidate.
- Each of 11 owners retains the same 8-connected component count and RETR_TREE hierarchy, not merely the same union silhouette.
- Primitive ID, source owner, original RGB palette, renderer order and structural-support status remain unchanged.
- 30k candidate output and provenance JSONs are stored privately under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_MultiPointExact_20261009/extended_30000`.
- Original source scenes are not modified, and the public GitHub branch contains scripts and summary **only**, never source PNG or source ring coordinates.

**Original hard gate is still failed.** GC001 2,562 > 1,887 (675 over); Raden 1,507 > 1,412 (95 over). Shape count 40, whole-image original RGB error, 4x browser clipping, Safari, no face plate visual Golden remain separate gates. Code did not change production or authorize merge/deploy.

New tools: `stage8_multi_point_exact.py` and `stage8_multi_point_original_gate.py`. Next run targeted contour connectivity/block-replacement optimization on difficult GC001 hair, clothing and unknown owners, and test whether Raden's remaining 95 vertices can be eliminated **without** violating fully signed original-owner raster semantics.
