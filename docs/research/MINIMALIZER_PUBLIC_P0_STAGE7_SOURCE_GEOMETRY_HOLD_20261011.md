# MinimalizerPublic StructuralRecovery P0 Stage7 — source-exact primitive exploration (2026-10-11)

**RESEARCH PASS for pixel containment and reproducibility / VISUAL CANDIDATE REJECTED / PRODUCT HOLD.**

`web/static/public-source-geometry-p0.mjs` derives a small number of maximal axis-aligned source-contained rectangular primitives from *existing manually observed* and individually SHA-pinned feature masks; it performs no new semantic segmentation and does not invent missing geometry. Each rectangle is verified pixel-for-pixel inside its original mask, and historical face-mask intersections / overlaps between feature masks fail closed. Every rectangle counts four vertices. Inputs, original source PNGs, Stage04 masks, baseline Facet40, and production are not modified.

On frozen original GC001 and Raden evidence from Stage5 (private Drive), with max eight rectangles per observed feature, min 20 pixels per rectangle and total budget 160 vertices:

| source | observation | original pixels | retained pixels | coverage | rectangles |
|---|---|---:|---:|---:|---:|
| GC001 | bright goggle frame | 1,173 | 504 | 42.97% | 8 |
| Raden | bow midtone | 1,130 | 351 | 31.06% | 8 |
| Raden | bow shadow | 3,140 | 1,051 | 33.47% | 8 |
| Raden | corset/lacing midtone | 779 | 362 | 46.47% | 7 |

The limited rectangle representation creates very visible stair-step/block features and discards most of the bow evidence. This is not sufficiently shaped for human Golden: **do not substitute for Stage5 or deploy**. Candidate geometry counts: GC001 8 rectangles / 32 extra vertices, Raden 23 / 92. Both add to, rather than replace, inherited failing original Stage8 budgets.

Semantic labels still originate from user-unapproved manual ROIs, not signed source-part authorities. Future work: independently approved source masks, source-contour fitting with strict no-new-region proof, vertex-accounted rings, and actual face/arm/clothing silhouette repair.
