# Multi-vertex block-to-one-point exact Stage8 research (2026-10-09)

Continues Draft PR #338 after the first two-to-one integer-grid vertex relocation passes. Research-only signed original scene and official OpenCV filled even-odd raster semantics retained.

Two-phase block replacement trial: try replacing each 3–6 contiguous source contour vertices by one integer-grid vertex drawn only from the original endpoints and their midpoint/cross-coordinates. Accept a candidate only if the complete **unguarded** original owner raster is exactly identical. No generative image, new material, face details or owner topology changes.

| Research state | GC001 vertices | Remaining original cap overage | Raden vertices | Over cap |
|---|---:|---:|---:|---:|
| Frozen source Stage8 | 3604 | 1717 | 2370 | 958 |
| Prior 2-to-1 relocation round2 | 2324 | 437 | 1412 | 0 |
| Block 3–6 to 1, 12k trials per owner | **2292** | **405** | **1412** | **0** |
| Repeat block 24k trials per owner | 2292 | 405 | 1412 | 0 |

Independent original SHA-signed Stage8 **full 11-owner** revalidation PASSED: 0 raster pixel differences, identical 8-connected components, same RETR_TREE hole hierarchy, original primitive identity and color/palette kept. Private 2292/1412 candidates and audit JSONs remain in `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_VertexRelocation_20261009/block_replace`; the original Stage8 never changed.

**Clear limit:** repetition of the exact 3–6 block strategy produced no further improvement. GC001 still has 405 source-ring vertices over the historical cap; it is NOT a production pass. Raden reaches cap in its *candidate* ring representation, not necessarily as an authorized source-to-SVG migration. Pixel-center original replay is not proof of browser SVG 4x edge parity. The 40-shape full-scene, source RGB non-face MAE, Safari, Golden and user approval remain HOLD independently.

Next work on GC001 requires exploring different ring restructuring or a provenance-authorized representation, not blind repetition. No production merge or deployment.
