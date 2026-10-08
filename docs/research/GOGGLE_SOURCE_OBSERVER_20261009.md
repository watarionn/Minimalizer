# Goggles Source Observer (2026-10-09)

**Completed candidate evidence; segmentation FAIL-CLOSED, research only.**

Goal: independently extract genuine goggles material from canonical GC001 original, preserving bangs and hair. Previous research established Phase04 accessory mask 217 pixels at chest, not goggles, and the goggles ROI x=104..240,y=38..103 is only an observation window.

Code `tools/research/goggle_source_observer.py` measures source RGB/HSV candidates limited to that ROI; saves the original and three visually highlighted subsets plus their binary candidate masks and SHA manifest. This is **not a validated goggles segmentation** and should not be used directly as SVG paint or semantic label.

| Observed original-color candidate | Pixels | Intersection with Phase04 hair mask | With Phase04 face mask |
| --- | ---: | ---: | ---: |
| Cool cyan/blue | 121 | **121** | 0 |
| Warm yellow/glass | 1373 | **1284** | 0 |
| Bright white/frame | 919 | **919** | 0 |

Interpretation: the coarse old hair mask encompasses visible goggle-colored portions, but candidate colors are NOT exclusively goggles (warm orange hair overlaps heavily and bright colors may belong to non-goggle parts). In particular 89 warm candidates are outside hair; do not claim ALL warm are hair. Source candidate overlay image visually shows true goggles and surrounding hair/hat share color classes. The mask cannot be converted into a trusted goggles-only SVG without independent boundary/part observation. An output goggles image/path was intentionally **not** generated. No hair or face existing work was overwritten.

The verified source fringe and all clothing experiments remain unchanged. No generative art, full skin plate, or inpainting. Full-character SVG remains visually NO-GO.

Test `tests/test_goggle_source_observer.py` and previous related regression suites: **44 PASS**.

Approved canonical private Drive artifacts `chatGPT及びCodex用/Minimalizer/GoggleSourceObserver_20261009`, folder `1i1pIrxPJMnfe1a1h2mU1eLfgdHQSc1Fn`: original highlight board `goggles_source_candidates.png`, three candidate PNG masks and manifest.

**Next gate:** manually or through existing semantically supported observer classify exact *connected goggle frame/lens geometry*, review against source and separate underlying hair. This requires actual independently grounded segmentation evidence, not ROI fill or broad color threshold. Only then validate SVG layer precedence and spatial/source colors. A second Golden subject remains required before any production integration.
