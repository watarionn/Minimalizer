# Contour Raster Fidelity v1 (2026-10-08)

**Executed on actual GC001 image; small source-locked improvement, still HOLD.** Research only; production Local/Public/Worker unchanged.

The original middle/right inter-eye orange strand has **694 source-connected pixels**. V3 source-only SVG recovered 601 (86.60%) and lost 93 without drawing outside the original mask. Decreasing contour epsilon did not help. This stage holds geometry and original-derived RGB constant, varying only SVG coordinate translation and SVG raster resolution/downsampling.

| Coordinate offset | resvg output | PNG reduction | source covered | missing | non-source excess |
|---|---:|---|---:|---:|---:|
| 0 | 340 | direct | 603 | 91 | 1 |
| 0 | 680 | nearest | 588 | 106 | 7 |
| 0 | 680 | bilinear | 598 | 96 | 0 |
| 0 | 680 | bicubic | 601 | 93 | 0 |
| 0 | 680 | lanczos | 600 | 94 | 0 |
| +0.5px | 340 | direct | 601 | 93 | 0 |
| **+0.5px** | **680** | **nearest** | **603** | **91** | **0** |
| +0.5px | 680 | lanczos | 584 | 110 | 0 |

Best strict zero-extra trial: offset +0.5px, raster 680, nearest reduction; **603/694 = 86.89%, +2 pixels recovered compared with v3**. At 340px direct offset 0, 603 are covered but 1 false extra pixel, hence fails strict no-expansion gate. Renderer/resampling changes indeed affect visibility, but account for only a tiny improvement; **91 missing original pixels still require investigation**, likely including tracing contours through pixel centers, ignored tiny source components and topology. None should be asserted as proven yet.

Code `tools/research/bangs_contour_raster_fidelity.py`. Tests `tests/test_bangs_contour_raster_fidelity.py`. **21 affected research tests PASS** (raster, earlier epsilon, continuity, source bridge and no-face-plate regressions). PNG and SVG per variant plus contact sheet and JSON SHA manifest saved under `chatGPT及びCodex用/Minimalizer/BangsContourRasterFidelity_20261008/`, Drive folder `1mj4uVVcqCJFG9EUioj4iO2VxPwx0zldh`. Cloud-side sync to be confirmed separately.

No face/subject skin-colored plate, no generated hair/skin or neural rendering. The complete character and face remain unresolved and visually NO-GO. No change to MinimalizerLocal or MinimalizerPublic.

Next: test polygon pixel-footprint tracing (pixel-cell union boundary rather than OpenCV pixel-center contour) with hard no-extra-pixel gate and sensible vertex-count budget. Preserve this research and all previous results.
