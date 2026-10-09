# GC001 One-Piece Visor Source Annotation v1 (2026-10-09)

**Result:** Native 340px source-reviewed semantic part masks, exact-source palette Pixel-Cell SVG, and research full-character integration completed. **Local mask-to-vector geometry PASS / exact semantic boundary and full Golden HOLD.** Production unchanged.

## Foundational correction: visor is one continuous lens, not two lens objects

In the original 340×340 GC001 character art, the eyewear is a single curved wraparound tinted visor with a continuous pale external frame. The broad white diagonal band at x~145–160 is **a reflection inside the visor**, not proof of a left/right physical lens split. Independent design corroboration: the official high-resolution character image **Hyakuto-Kyoko_pr-img_01.webp** from the user-provided `HoloMenImages.zip` (2000×2000, SHA-256 `7300bf4f9b2baf4dd5452448bb9ec460004e82763a22a2eeecba4057d7b1c1a5`) has the same one-piece visor construction in a different pose. **Do not copy or geometrically project that different-pose asset into GC001**. It is only independent structural evidence. Earlier multi-turn attempts to discover two semantic goggles lens instances were built on a faulty topology assumption.

## Source-reviewed mask contract

`tools/research/goggle_single_visor_annotation.py` holds manually source-reviewed outer and inner control polygons based on native and magnified **340×340 original pixels**. These are a transparent, repeatable human-reviewed *visible-region hypothesis*, not independently proven pixel-perfect semantic ground truth. The code explicitly forbids any region at y>=100, so it does not intersect the certified inter-eye bangs (ROI y=100–140). No hidden goggles volume or under-hair material is invented.

- Total outlined visible visor: **2,680 source pixels**.
- Inner **single lens**: **1,663 source pixels**.
- External white/silver **frame**: **1,017 source pixels**.
- Lens and frame masks mutually exclusive, their union exactly matches the outlined region.
- Original RGB-medoid color-cluster SVG generated separately for lens and frame using Pixel-Cell boundary contouring epsilon 0.35: lens **4 actual color paths / 425 vertices / 11 contours**, frame **4 paths / 495 vertices / 13 contours**. No raster embedded inside SVG; no neural fill.
- Rendered isolated source-annotation SVG at native 340px covers **2,680/2,680 annotated pixels**, with **0 output pixels outside that annotated outline**. **This is polygon-to-SVG fidelity, NOT semantic segmentation accuracy against external truth**.
- Research full-scene composition using prior `GoggleClothingSourcePoC_20261009/source_tonal_clothing_scene.svg`: changed **2,698** rendered RGB pixels, **0 outside annotated visor plus 2px AA neighborhood**. The exact prior **3 certified inter-eye fringe paths** are byte-identically preserved.
- Real source/annotation/before/after 4-panel PNG inspected. The new visor is recognizable as a one-piece golden reflective lens with a pale border. The overall person is still visually **NO-GO** owing to the unresolved blank face and fragmented rest of the art.

## Gate / outputs

**78 affected research regression tests PASS**, including existing face-plate, fringe, hair/clothing and goggles observation suites. No deployment to MinimalizerLocal, Public or Worker, no changes to their release gates.

Artifacts in private canonical Drive `chatGPT及びCodex用/Minimalizer/GoggleSingleVisorAnnotation_20261009` folder `15KTwOd5EqvUVJBOKUZAYxPLnyLimcDTJ`:
- `compare_onepiece_visor_scene.png` source, manual part review, previous character, research character
- `visor_observed_outer.png`, `visor_lens_review.png`, `visor_frame_review.png`
- `source_visored_onepiece.svg`, `source_visored_onepiece.png`
- `research_part_scene_with_visor.svg`, `scene_before_visor.png`, `scene_after_visor.png`
- `manifest.json` SHA-256 and provenance

## Next meaningful stage

Audit manual annotation accuracy at *actual visible edges* (not self-IoU), compare original-source rim/lens/white reflection local color residuals, and test on another genuinely independent character before generalization. Do not endlessly retune the same box/color threshold; preserve source-owned composition. More importantly, prioritize the intentionally empty face and incomplete body once the visor gate is stable. Never reinstate a giant skin plate, generate new faces, or extrapolate under-hair eyewear.
