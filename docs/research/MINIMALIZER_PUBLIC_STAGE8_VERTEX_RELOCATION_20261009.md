# MinimalizerPublic Stage8 exact-grid vertex relocation (2026-10-09)

**Milestone: Raden research candidate reaches historical signed Stage8 ring vertex cap, 1,412.** No signed original scene file changed. This is **not production authorization**.

A new conservative 2-to-1 integer-grid vertex relocation search attempts several locations derived only from two existing contour vertices. Candidate is accepted only if the entire owner polygon official OpenCV single-pass even-odd **unguarded** 340x340 raster is bit-for-bit identical. No source pixels or RGB colors generated.

Starting from independently original-verified campaign candidates GC001 2,479 and Raden 1,449:
| Research candidate | GC001 | Raden |
| --- | ---: | ---: |
| Frozen original Stage8 | 3,604 | 2,370 |
| Campaign before relocation | 2,479 | 1,449 |
| Relocation pass 1 | 2,327 | 1,416 |
| Relocation pass 2 | **2,324** | **1,412** |
| Historical vertex cap | 1,887 | **1,412** |
| Remaining overage | **437** | **0** |

Each relocation pass was independently compared to the full original signed Stage8 geometry and all 11 owner source rasters, with zero changed unguarded pixels, 8-connectivity and contour-hole RETR_TREE matching, palette and primitive owner identity unchanged. Repro scripts under `tools/research/public_geometry_js/stage8_vertex_relocation.py`. Private versioned candidate and SHA-pinned signed original revalidation evidence under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_VertexRelocation_20261009/round2/`.

**Important technical distinction:** Raden has *candidate* source-ring budget pass under the exact original OpenCV 340x340 pixel raster, not a rewrite of immutable source Stage8 history or automatic PASS of the production gate. Browser SVG serialization, DPR1/4, 40-shape full-scene, GC001 nonface RGB MAE, face-parts hidden, Safari Golden and human Golden must be separately validated. Do not merge or deploy research branch.

Next stage: GC001 437 vertex gap needs new candidate construction; prioritize hair / unknown / clothing with full owner exact mask replay. Raden should undergo browser SVG and original source alpha/Golden checks before any attempt to promote.
