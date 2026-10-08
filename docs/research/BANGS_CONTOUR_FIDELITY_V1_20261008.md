# Bangs Contour Fidelity v1 (2026-10-08)

**Research execution complete; contour simplification-only fix NO-GO. Production unchanged.**

User requests restoring the observed central/right forehead bang in GC001. Previous v3 evaluated complete connected original-source orange hair component at 694 pixels, of which only 601 were recovered by source-only SVG alpha, missing 93. This stage isolates one variable: contour simplification epsilon. For the same original image, existing source-only tonal class layers, isolated resvg renderer, alpha downsampling and measured mask, compare epsilon=0.6, 0.3, 0.0. No generated hair, facial fill, face/subject skin plate, neural image generation, production Worker or Public modifications.

## Actual measured results

| Epsilon | Contours | Vertices | Source covered | Missing | Excess |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0.6 | 8 | 102 | **601 / 694 (86.60%)** | 93 | 0 |
| 0.3 | 8 | 192 | 597 / 694 (86.02%) | 97 | 0 |
| 0.0 (no simplification) | 8 | 379 | 597 / 694 (86.02%) | 97 | 0 |

**Conclusion:** lower epsilon did not restore 93 lost source pixels. The existing 0.6 is the best of the three zero-excess variants. The loss cannot be attributed solely to simplification. Candidate causes to separately measure include component contour representation (cv2 contour line through pixel centers; fill conventions), 680→340 alpha resampling (Pillow default interpolation), and small detail polygons filtered by `cv2.contourArea < 3`. Do not claim any of these causes confirmed without experiments. This stage does not claim visual improvement.

Script: `tools/research/bangs_contour_fidelity_v1.py`; tests: `tests/test_bangs_contour_fidelity_v1.py`. Exact input source/masks validated by existing research loaders. Every candidate SVG and raster PNG has SHA-256 in `manifest.json`, together with per-row measured original-versus-output coverage. Total **18 tests PASS** including v3/v2/bridge/no-face-plate guard suites.

Private canonical Drive folder: `chatGPT及びCodex用/Minimalizer/BangsContourFidelity_v1_20261008/`, Drive folder ID `1sXwTZzb7AHGCw4dCtkUs-q9wzAqYEQF3`. Includes 3 SVGs, 3 PNGs, full comparison PNG and manifest. Verify server-side synchronization independently if needed.

## Next gate
Do a controlled **contour coordinate/pixel-center representation and rasterization** comparison at constant source mask/epsilon. Measure coverage and excess explicitly without inventing original hair geometry or broadening masks. Accept candidate only if source coverage increases with zero or demonstrably acceptable excess, plus low contour/vertex budget. The unresolved face remains NO-GO. Do not deploy into MinimalizerLocal/Public before independent source and full Golden gates.
