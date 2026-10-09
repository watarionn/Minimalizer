# GC001 Goggle Gap Semantic Owner Correction (2026-10-09)

**Real original-source + saved masks audit completed; semantic depth/occlusion remains HOLD.**

This stage corrects a mistake in PR283's interpretation. The orange samples between upper-head goggles' three pale rim components were described as "front bangs", but the independently certified inter-eye strand has a strict source ROI **y=100..140**, and the gap samples in this audit are near **y=59..65**. Color alone is not a semantic part label.

On original GC001 source SHA256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`, with the saved 785-pixel goggles pale candidate mask, the source Phase04 masks and independent certified inter-eye source fringe, actual sampled intersections were:

| Gap pair | Source orange samples | Legacy Phase04 hair ownership | Phase04 face ownership | Verified inter-eye fringe ownership |
| --- | ---: | ---: | ---: | ---: |
| 0–1 | 0 / 4 | 4 / 4 | 0 | **0** |
| 0–2 | 24 / 35 | 27 / 35 | 0 | **0** |
| 1–2 | 8 / 11 | 11 / 11 | 0 | **0** |

Significant warning: **even all four pale source pixels in 0–1 appear in the old "hair" mask**. That old mask demonstrably absorbs goggles, so its hair label cannot prove a 3D foreground hair layer or hidden-frame geometry. Orange source at y~59 may be hair, goggles material, or adjacent hat depending on source; none has independent per-pixel semantic depth confirmation in this step.

Actual magnified source evidence `gap_semantic_owner_review.png` shows each shortest-gap sample point on the original, without drawing a bridge. The source observations are valid, and the earlier claim that certified central bangs own the gaps is **formally corrected**. No independent full goggles lens/frame segmentation achieved, no material depth occlusion verified, no replacement SVG, no subject-wide skin ellipse, no generative fill or edits to MinimalizerLocal/Public.

Script `tools/research/goggle_gap_owner_correction.py`, regression `tests/test_goggle_gap_owner_correction.py`, plus previous goggles/face safeguards: **73 PASS**. Actual manifest and image live at approved private Drive `chatGPT及びCodex用/Minimalizer/GoggleGapOwnerCorrection_20261009`, folder ID `1UQb9JPjB2KrIvoktgbxatmt1xVsX3iKY`.

Next gate: source-reviewed *semantic boundary ownership* at the short pale gap and two warm gaps, with explicit goggles lens/rim vs hair/hat negative examples and independent observation. Do not start another nearest-neighbor paint/dilate loop or turn hair-mask membership into depth claims.
