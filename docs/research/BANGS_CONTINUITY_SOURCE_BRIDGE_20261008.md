# Bangs Continuity Source Bridge (2026-10-08)

**Status:** source-observed central/right fringe repair implemented, compared visually and tested, but **overall style quality remains HOLD / NO-GO for production**.

## User-specific visual fault, not a general face-hole issue
The original GC001 shows an orange hair strand occupying the space between the eyes, running down from the central fringe. In the prior vector image its right half ends abruptly. Earlier assistant diagnoses mistakenly discussed goggles, fringe gaps or false skin plates without checking the exact pixels the user pointed out.

## Root cause verified at original-pixel coordinates
From the existing Phase04 Kyoko hair and face masks, rows **y=112 through y=132** in source region **x≈145–185** are assigned **face**, even where the canonical original RGB is visibly orange hair (e.g., source RGB around x=170,y=120 is `[235,108,43]`). Hair-owner priority alone cannot restore an area where the original reference hair mask is **false**.

Script `tools/research/bangs_continuity_source_bridge.py` uses a narrow **manual GC001 ROI** `x=144..185,y=100..140`, source-only orange chroma/brightness thresholds, an 8-connected source region, and a verified head-to-between-eye bridge. No source pixels are invented.

- Observed orange source component: **694 pixels**, contiguous.
- Portion missed by hair mask but owned as face: **390 pixels**.
- Repair geometry: **2** original-source-derived SVG contours, **40** vertices.
- Repair source RGB `[234,108,43]` is an **actual RGB value from the original missed orange region**, not an interpolated/generated color.
- Appended to previous `RemoveSkinUnderlay` SVG as **hair**, no subject-wide skin plate, no face layer, no embedded image or new eye/nose/mouth structures.
- Real rendered previous vs current change: **574 pixels** including vector rasterization aliasing; area of changes is constrained near the verified orange component. Existing face remains unresolved, not a complete character render.
- The repaired bang is still visibly **too narrow and stylized** versus the reference, and the subject/clothes have broader issues. **Do not present this as complete bangs, silhouette, or facial fidelity PASS.**

## Evidence and regression

Canonical saved artifacts in `chatGPT及びCodex用/Minimalizer/BangsContinuity_SourceBridge_20261008/`, Drive folder ID `1u5ewp7RmxqVDBsnfAeO_LCnQXtKMMHkV`:
`repaired_bangs.svg`, `repaired_foreground.svg`, PNG renders, `comparison_bangs_continuity.png`, `manifest.json` with exact SHA-256s.

`tests/test_bangs_continuity_source_bridge.py`, together with existing face-hole and implicit-face-plate gates: **9 tests PASS** on Windows research interpreter.

## Next

1. Compare connected hair mask plus color edge geometry against the **source strand widths per horizontal scanline**, not just one connected-source component. Original hair is not a single flat source orange tone, so preserve source-observed hair shadows/highlights as bounded subregions where supported.
2. Reconcile the Phase04 face/hair partition with original-observed fringe before vectorization, then test whether the strand is continuously represented across y=108..134 and matches the source endpoints. Do not silently overwrite the canonical Phase04 mask; save a derived repair mask.
3. Restrict changes to this strand; preserve previous no-full-skin-plate regression.
4. Keep Local PWA/Public unchanged until an independent second character and full Golden path/color/silhouette gates pass.
