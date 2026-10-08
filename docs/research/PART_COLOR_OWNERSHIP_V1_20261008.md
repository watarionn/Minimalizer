# Part Color Ownership v1: RGB distance overflow fix (2026-10-08)

**Status:** Real GC001 improvement verified, Core/production quality HOLD. No live deployment.

The earlier full SVG prototype `tools/research/face_parts_vector_scene_v1.py` produced almost-white hair and disordered dark costume blocks despite source masks and capped source-derived palettes. Root cause identified inside `region_colormasks()`: the difference vectors were cast to **signed int16**, then **squared as int16** by NumPy. RGB differences whose squared value exceeds 32767 wrap around, leading to incorrect "nearest color" assignments (the source sample classification becomes wrong). This was a concrete mathematical bug, not merely a suboptimal artistic palette.

## Controlled fix
Research-only fork `tools/research/face_parts_vector_scene_color_fixed.py` (original production/research baseline not silently replaced). Replace squared Euclidean channel differences with **int32 deltas, int32 products and int64 accumulation**, guaranteeing exact non-overflow RGB distance for 8-bit channels. Source medoid palettes, mask provenance, face-feature exclusion, source-observed tie region, SVG geometry and output verification remain otherwise identical.

## Real comparison (same canonical GC001 source)
| Metric | Previous uncorrected | Corrected |
| --- | ---: | ---: |
| SVG elements | 27 | 27 |
| Vector contours | 290 | **221** |
| Total vertices | 5,489 | **4,188** |
| Source foreground silhouette IoU | 0.97584 | **0.97579** |
| Foreground pixels outside source | 186 | **186** |
| Missing source foreground pixels | 1134 | **1137** |

**Visual result:** hair regained orange identity and navy/white costume sections became much more readable. This is a strong improvement over the initial white hair, but **not an artistic/Golden PASS**: broad pale blank face persists and hair/costume still contain gaps; silhouette fidelity did not improve. The RGB overflow fix unexpectedly also reduced unnecessary color fragments and vector vertices.

Output comparison SHA-256: `3c7007f7fbf56d172a67872cc66ad9fe4718f3857e97128f57a82ff9c2788a11`.
Private folder: `chatGPT及びCodex用/Minimalizer/PartColorOwnership_v1_20261008/` (Drive ID `1Pl1eElxVCmlKqKHjVf2nK3X6qTja1con`), including vector SVG, raster PNG, transparent foreground, comparison and manifest with artifact hashes.

## Gates and remaining work
- New `tests/test_part_color_ownership_v1.py` verifies large RGB distance 255² does not overflow, source orange remains dominant in a synthetic orange-color part, medoid RGB belongs to observed input, and research-only execution.
- Affected Local/Public/Browser/ZeroBase test suite run separately and must pass before merge; production Minimalizer itself has not changed.
- Next: improve negative space/occlusion and owner arbitration for face hair, shoulders and clothing, while reducing 4188 SVG vertices. Source foreground IoU/left-right arm structural gates still HOLD. The new implementation remains **GC001-only** and may not be generalized without another character test.
- Facial eye/brow/nose/mouth geometry was not constructed. A plain skin-colored figure silhouette remains; **do not treat this as an answer to the user's desire for naturally simplified face parts**.
