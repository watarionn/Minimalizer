# Bangs Full-Strand Continuity v3 (2026-10-08)

**Status: research source-strand comparison completed; overall visual quality HOLD, not a production or Core Golden pass.**

## Goal
The owner identified the right-central forelock abruptly cut off between the character's eyes. The earlier 390-pixel source bridge was insufficient. This stage checks the **entire 694-pixel contiguous original orange strand**, using actual original row widths and excluding all skin-wide underlays or hallucinated hair.

## Changes
- Code: `tools/research/bangs_full_strand_continuity_v3.py`
- Source: canonical GC001 340×340 original, with hash and source masks validated by the prior verified loaders.
- Source-derived region: prior `extract(...)` entire 694-pixel 8-connected original orange component in a deliberately narrow Kyoko-only ROI, rather than just the 390 pixels misclassified as face.
- Prior v2 repair paths are replaced, not stacked. Three source-cluster LAB tonal classes with RGB values snapped to actual pixels; tiny accent components without valid polygon are skipped. No generative models, new hair extrapolation, face color fill, subject underlay or embedded raster.
- Crucially, the **SVG-only fringe component is rasterized separately** to compute honest source-versus-vector coverage, not inferred from color pixels in the preexisting full character rendering.
- Source row comparison for y=106..140 saved in JSON: source width/span, actual rendered source pixels and coverage for each row.

## Real GC001 evidence
- Input: **694** source-observed connected orange hair pixels, including **390** previously misclassified as face.
- Output standalone SVG reproduced **601 of those 694** source pixels: **86.60% source coverage**, still missing 93 pixels. **0** rasterized fringe pixels outside its original connected source region. Thin strand ends/edge pixels are lost during contour simplification/rasterization.
- **3** tone layers, **8** contours, **102** vertices.
- Total SVG render differs from previous v2 in **807** pixels near the source-observed strand, **0** changes outside a two-pixel fringe neighborhood.
- Actual side-by-side image still shows overly simplified or missing sections; no claim of complete source width, hairstyle fidelity, corrected whole silhouette or face reconstruction.
- Input full-character still has an intentionally unresolved/blank face; this is research evidence only.

Files under canonical private Drive `chatGPT及びCodex用/Minimalizer/BangsFullStrandContinuity_v3_20261008/` (folder ID `1YGajQjDMyWBhzLLQIE77DXi9naggdEL7`): `whole_full.svg`, `whole_foreground.svg`, `source_component_only.svg`, rendered PNGs, `comparison_full_fringe_v2_v3.png`, `manifest.json` (source per-row data and exact output SHA hashes).

## Tests and next gate
`tests/test_bangs_full_strand_continuity_v3.py` plus v2, source bridge, face plate and skin-underlay regression suites: **15 tests PASS**.

Next should specifically reduce the **93 missing original fringe pixels** by evaluating vector contour simplification epsilon, source mask topology and rasterization at native 340 resolution; find a measured shape improvement without source-pixel expansion. Separate source strand visibility from global figure/color and maintain original-source-only RGB and no-subject-face-plate invariants. Check on another subject before any generalized implementation. No changes to MinimalizerLocal or MinimalizerPublic.
