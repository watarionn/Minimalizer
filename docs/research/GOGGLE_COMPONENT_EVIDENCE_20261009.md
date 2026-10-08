# Goggle Component Evidence (2026-10-09)

**Completed source-constrained segmentation proposal study; independent lenses/frame semantic verification NO-GO.**

Continues PR271 on original GC001. Existing 217px accessory mask is at chest, not goggles, and original hair mask overlaps observed goggle materials. Used OpenCV GrabCut source pixels with distinct conservative manual clue windows, not semantic class detector or verified polygon labels. The windows *are not ground truth* and definite foreground seeds influence the output.

| Candidate | Pixel count | Already assigned to hair | To face |
| --- | ---: | ---: | ---: |
| left lens | 1,708 | 1,560 | 0 |
| right lens | 1,645 | 1,562 | 0 |
| frame | 5,648 | 4,939 | 0 |

Source-image side-by-side clearly shows candidate windows include adjacent hair and hat; notably the broad frame proposal is mostly an unvalidated region. Do **not** paint the entire proposal as goggles or report these pixels as actual lens/frame segmentation. Export only proposal alpha PNGs, contact sheet and auditable SHA manifest, **no goggles SVG and no production changes**. Existing corrected inter-eye bangs and full-character source-owned SVG remain untouched.

Code `tools/research/goggle_component_evidence.py`; `tests/test_goggle_component_evidence.py`; **48 relevant regression tests PASS**.

Canonical private Drive `chatGPT及びCodex用/Minimalizer/GoggleComponentEvidence_20261009` folder ID `1z6NWVwqn78igVjVpLyYUVzilWWNSrgkt`.

**Next action:** seek existing true semantic segmentation model/output for glasses/goggles, or use source-reviewed human polygon annotations for the visible pair of lenses and frame. Boundary evidence should exclude neighboring orange hair and red hat before generated SVG layer replacements. Not yet a usable production step and overall Golden stays HOLD.
