# Bangs Source Tonal Width v2 (2026-10-08)

**Executed research PoC; local fringe geometry and original color provenance PASS, overall character rendering HOLD/NO-GO. Production Local/Public unchanged.**

## User's precise visual observation
The original reference has a center-right orange bang crossing the gap between the eyes. Prior SVG erroneously cut it because Phase04 hair mask calls that part of the source `face`. PR #257 restored 390 observed original-orange pixels as a single-colored bridge; user asked to preserve the strand's width and tonal shading next.

## This stage
`tools/research/bangs_source_tonal_width_v2.py` reuses the exact GC001 original and the already-verified, GC001-only manually localized source connected-orange region, rather than generating new strands. It replaces **only** the v1 appended fringe bridge SVG element, leaving other SVG elements and the unresolved face untouched.

In the 340×340 canonical coordinates, repaired-source-strand widths by row (not arbitrary spline expansion) are:
`y=110:7, 112:25, 114:23, 116:22, 118:19, 120:19, 122:19, 124:16, 126:15, 128:15, 130:7, 132:5, 134:2` pixels. These are measured *only for missing hair pixels currently misclassified as face*. They are not the entire original hair width on every row.

The source-only missing-region RGB values are grouped into three LAB color classes (deterministic fixed seed), and each representative RGB is snapped to an **actual pixel observed in that strand**, not the generated cluster center. Tiny accent islands without a faithful closed polygon are skipped rather than invented. Output is **2 SVG layers, 3 contours, 51 vertices**, compared with prior single-color **2 contours, 40 vertices**. A prior initial attempt failed closed on an unvectorizable tiny accent and was repaired to skip such tiny accents.

- Original misclassified source strand: **390 pixels**, connected source-orange component: **694 pixels**.
- Real raster change from preceding single-tone SVG: **448 pixels** including anti-aliasing, confined to a 2px neighborhood of the source-observed fringe; **0 out-of-region changes**.
- The v2 fringe looks somewhat more naturally toned but **the difference is small**. The complete Kyoko render still has a large missing face and other garment/hair problems. Do not claim visually complete foreground or general-purpose face/hair recognition.
- **No broad face/subject skin polygon, no invented skin under facial features, no neural model or missing-hair synthesis.**

## Verified artifacts and checks
Canonical private folder: `chatGPT及びCodex用/Minimalizer/BangsSourceTonalWidth_v2_20261008/`, Drive folder ID `1uUTzNsxJqXGL1RFA8uir5E8-hjyIxNcy`.

Files: `tonal_full.svg`, `tonal_foreground.svg`, their PNG renders, `comparison_bangs_v1_vs_v2.png` (reference/one-tone/v2), `manifest.json` with SHA-256 for all generated images and vectors, palette provenance and per-row widths.

Regression suite `tests/test_bangs_source_tonal_width_v2.py` + previous fringe/face-hole/face-plate tests: **11 PASS**. No code deployed to production.

## Next
1. Verify the complete original hair strand (not just the missing face-owned pixels) and retain multiple source-observed neighboring strands, if source segmentation evidence warrants it.
2. Record width and connectivity at each original source row and test if the current vectorized path has clipped/stranded pixels or faithfully matches the actual observed source.
3. Do not treat the face hole as a good look. Reconstruct a fully observed, part-owned vector character only after independent source geometry and the no-face-plate gate pass.
