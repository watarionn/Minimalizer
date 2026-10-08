# Hair-Wide Pixel-Cell Audit (2026-10-09)

**Research audit complete, Golden/production status HOLD.**

The canonical GC001 Phase04 hair mask was not modified. The source-only, owner-observed center/right inter-eye orange fringe has 694 contiguous original pixels, of which exactly 390 had been classified as face instead of hair. Only those 390 independently verified face-misclassified pixels were added to a **derived** hair mask. Unrelated portions of the 694-pixel orange component were explicitly **not** reassigned. This corrected an initial fail-closed check when the proposed broad union added more than the verified 390 pixels.

Masks: original **14,654** pixels; derived **15,044** pixels.

At the original 340×340 raster resolution, SVG pixel-cell tracing results were:

| Mask | epsilon | Covered | Missing | Excess | Vertices |
|---|---:|---:|---:|---:|---:|
| original | 0 | 14,563 / 14,654 | 91 | 0 | 2,448 |
| original | 0.35 | 14,604 / 14,654 | 50 | 0 | 1,447 |
| original | 0.6 | 14,359 / 14,654 | 295 | 0 | 787 |
| derived | 0 | 14,949 / 15,044 | 95 | 0 | 2,610 |
| **derived** | **0.35** | **14,991 / 15,044 (99.65%)** | **53** | **0** | **1,538** |
| derived | 0.6 | 14,733 / 15,044 | 311 | 0 | 840 |

Script: `tools/research/hair_wide_pixel_cell_audit.py`.
Tests (new plus relevant older hair/face plate regression suites): **33 PASS**.

Evidence artifacts under private canonical Drive `chatGPT及びCodex用/Minimalizer/HairWidePixelCellAudit_20261009` folder `1Jh5MJiuIGp6Ttk4vupkA3EIwG1J2NFDS`: six independent hair SVGs, six PNGs, a source/previous-incomplete-scene/source-hair footprint comparison, derived binary hair mask and manifest with variant metrics and SHA-256s.

**Interpretation guard:** 99.65% is ONLY *derived binary hair-mask footprint* reproduction, not full color-shaded hair, not accessory-overlap, face, uniform, or overall image quality. Hair-only preview is monochrome by design and must NOT be blindly overlaid as one solid orange slab over goggles/face. Prior manually verified three-shade central fringe remains in prior research part-scene. The source faces remain unresolved and whole-character Golden has NOT passed; production Local/Public unchanged.

Next: preserve the original hair/part occlusion relationships and source-derived tonal regions while selectively using pixel-cell contour tracing; explicitly measure isolated and composite-render hair mask, goggles/face overlap, RGB errors and whole-character Golden before deployment. Never add a broad skin plate or guessed hair.
