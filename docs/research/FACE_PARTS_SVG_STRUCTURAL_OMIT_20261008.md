# Face Parts SVG Structural Omission / 2026-10-08

**Status:** Real canonical GC001 experiment PASS for structure-only omission, **Core quality HOLD**. User correctly rejected prior face-wide overlays and approved researching SVG-only exclusion of facial features. This PoC performs no face/background fill whatsoever.

## Inputs and implementation

- Exact original Kyoko GC001 SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.
- Repository source Phase03/04 foreground / hair / facial masks; prior Face Parts Only v1 original-observed eye/nose/mouth component masks. Brow detection remains unverified.
- Code `tools/research/face_parts_svg_structural_omit.py`. It extracts source-observed Canny edge polylines, simplifies them minimally with OpenCV and rejects **entire paths intersecting a confirmed facial micro-component mask**, except protected hair. The SVG contains ONLY unfilled strokes. There are no face circles, polygon skin masks, raster embeds, invented missing pixels, or image generation model calls. Existing research-only resvg adapter makes the preview; nothing is installed in production.
- This is **a transparent stroke layer, NOT a complete character SVG render**. A white background is used solely for viewing its PNG preview. Displaying this SVG over the ORIGINAL photograph necessarily reveals the original face parts below the transparent omitted strokes. Final omission will require a true no-feature base vector representation rather than raster concealment.

## Real evidence

Canonical 340×340 GC001 execution yielded:
- Candidate original-derived paths 201
- Paths retained **185**
- Paths excluded for observed face feature intersections **7**
- Other filtered paths **69**
- Total original-observed face feature mask pixels **174**, protected hair overlap **0**
- SVG SHA-256 `9e406054e451a3798fc7385b17c16db72e26f08b5d8cc55f3255faa9ffa06342`
- Original versus structural SVG preview SHA-256 `1ecc07ba7fc42fff19adb54939db3167904fc7c7e5689cb5d342bba19d4e1274`

Important: since contours can straddle face/hair boundaries, dropping full stroke paths can remove unrelated source edge sections. The white-background preview still shows some brow/cheek-like marks. Therefore **do not claim all facial detail suppression or Core Golden PASS**.

## Gates

`pytest tests/test_face_parts_svg_structural_omit.py tests/test_face_parts_only_v1.py tests/test_semantic_art_mixer_v3_source_masks.py tests/test_semantic_art_mixer_v2_guarded.py tests/test_semantic_art_mixer_v1.py -q`: **35 passed**.

Saved under `chatGPT及びCodex用/Minimalizer/FacePartsSVG_StructuralOmit_20261008/`, Google Drive folder `1BRSzLeB7t-UR-BkMNtDGgl25wM0blXWl`. Files `observed_strokes_excluding_face_parts.svg`, `transparent_svg_preview.png`, `comparison_original_vs_structural_svg.png`, and `manifest.json`. Cloud sync should be independently verified.

## Next

Build source-part-conditioned vector foreground regions (not an original-image overlay), then enforce facial detail omission at path assembly, including brows and dark-line semantic verification. Avoid deleting hair/face boundaries via an entire mixed-purpose path. A separate whole-character silhouette/topology and color budget validation must precede any Local PWA or Public integration.
