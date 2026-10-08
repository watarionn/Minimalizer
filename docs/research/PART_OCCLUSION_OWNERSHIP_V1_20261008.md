# Part Occlusion Ownership v1 / Minimalizer research (2026-10-08)

**Status: foreground ownership partition implemented and run on real GC001, visual quality HOLD / NOT promoted to production.**

## Background
Prior `Part Color Ownership v1` fixed the mathematically incorrect signed-int16 squared RGB distance, recovering orange hair and navy/white clothing. Nevertheless, the full SVG still has missing hair/garment islands and source-part masks overlap. This experiment explicitly partitions the source-visible foreground so that a given pixel is owned by one semantic role.

## Changes and ownership constraints
Reproduction: `tools/research/part_occlusion_ownership_v1.py`. It is an isolated research fork of `face_parts_vector_scene_color_fixed.py`, **not** a live production replacement.

- The exact GC001 source and aligned Phase03/04 semantic masks are loaded and their source SHA/provenance checked through existing loaders.
- The observed green necktie and visible skin **excluding source hair** are reserved first. The hair exception is essential: bangs crossing the coarse face mask remain source-owned hair, rather than being displaced by skin-colored subject underlay.
- Remaining pixels are assigned once, using priority `accessory > hair > left arm > right arm > major clothing > neck > torso > lower body`. A final source-pixel residual mask covers unassigned non-face foreground. Its rendering uses existing source RGB palette members only.
- Per-part palettes are based on original source pixels, with the int32/int64 squared-distance fix retained. No facial eye/nose/mouth/brow geometry, face-sized overlay polygon, img2img, Generative Fill, missing anatomy synthesis or raster SVG embeds.
- The partition is recorded per role in `manifest.json`; no claim of perfect role masks or automatic identity understanding.

## Real result and quality decision

| Observed measure | Prior source palette corrected | New ownership partition |
| --- | ---: | ---: |
| SVG path elements | 27 | **31** |
| Combined contours | 221 | **244** |
| Total vertices | 4,188 | **4,616** |
| Foreground silhouette IoU | 0.97579 | **0.97593** |
| Foreground false positives | 186 | **188** |
| Missing source foreground pixels | 1,137 | **1,127** |

The reference subject has 54,450 pixels. 52,442 are reserved to face/necktie and explicit semantic owners; **2,008** are residual source-owned pixels that should not remain skin-colored by accident. Part owner counts: hair 14,654, left arm 2,717, right arm 5,923, major clothing 3,685, neck 1,996, torso 5,760, lower body 10,898, accessory 41.

**Visual outcome: HOLD**, not final quality PASS. Hair, outfit and chest lines still contain thin gaps and fragments, and the face remains expressionless, although the per-pixel ownership and source/hair priority are explicit. Vertex/path count **increased** by 428 vertices / 4 elements; previous low-shape budget target was not met. IoU improved by only 0.00014. Treat this as an evidence-preserving intermediate, not a substitute for the prior color-corrected experiment. The garment/source color match should be examined region by region, not inferred from mere owner-mask overlap.

Output canonical private Drive folder: `chatGPT及びCodex用/Minimalizer/PartOcclusionOwnership_v1_20261008/`, folder ID `1VafQ5DtNgDEu4j5-XxxU4vCESeY27KQI`.

Contains `character_part_vector.svg`, `character_foreground_alpha.svg`, two PNG renders, `comparison_source_vs_vector.png` and `manifest.json`. Comparison SHA-256 `db96fc82920e5388597a0aef7f0207d9900ec78cabe09ccf943c78c2ec7352dc`. Drive-mounted source is verified; cloud sync independently checked separately.

## Next engineering action
1. Diagnose contour vectorization losses (small connected components omitted by area cutoff, anti-aliased boundary/rasterizer behavior) independently from part priority.
2. Add pixel-level provenance or silhouette-mask-constrained raster/geometry post-validation before reducing a region to polygons; preserve arm-torso negative spaces and orange bangs.
3. Constrain tiny-island merging, keeping only source-observed geometry and color. Require fewer vertices than the proven color-corrected baseline without lowering silhouette quality.
4. Keep all artifacts as research; Local PWA/Public and Core remain unchanged. Separate character and Golden gates required before promotion.
