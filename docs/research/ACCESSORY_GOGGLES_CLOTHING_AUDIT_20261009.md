# Accessory Goggles Clothing Audit (2026-10-09)

**Research diagnostic completed. No changes to MinimalizerLocal/Public.**

The previous Phase04 accessory mask contained only 217 pixels, and the earlier role-alpha audit found 202 missing. This task checked the original accessory mask's actual position instead of falsely assuming it represents the character's goggles.

## Actual GC001 findings

- Source accessory mask: a single 8-connected component, **217 pixels**, bounding box **x=180..200, y=214..244** (x,y,width,height = [180,214,21,31]).
- An explicitly approximate *goggles diagnostic window* (x=104..240, y=38..103) intersects that mask in **0 pixels**. This manual rectangle is **not ground-truth goggles segmentation**. Therefore the earlier 202-pixel accessory SVG deficit measures a lower-body chest-region decoration, NOT absent goggles. Do not infer any actual goggles geometry or source color from this mask.
- Existing clothing mask deficits in source-part-only SVG alpha were 686 pixels for major clothing and 2,071 for lower body (PR #267). When source original masks are independently traced using Pixel-Cell 0.35, major clothing is **3705/3737 covered, 32 missing, 0 outside, 574 vertices**, and lower body is **12560/12563 covered, 3 missing, 0 outside, 200 vertices**. This is **binary geometry only**, not source-color preservation nor successful full clothing reconstruction; these isolated SVGs are diagnostic colors and must not be merged into production.

## Consequences and next gates

1. Build an independent **source-observed goggles annotation** with precise pixel boundaries, manually verified against the original, without inventing hidden material; validate goggles mask overlap with original hair, face and existing SVG part masks. The accessory_or_held_object mask is not a goggles segmentation.
2. Apply pixel-cell to separate original-source color-owned clothing regions and verify real composite RGB/occlusion; never put a giant blue single-color garment rectangle over the character.
3. Keep high-fidelity certified inter-eye fringe paths and original layering unchanged, reject face/subject skin-colored plates. Face remains unresolved, overall character not Golden PASS.
4. Verify on an independent second input before rollout.

Actual source and output under `chatGPT及びCodex用/Minimalizer/AccessoryGogglesClothingAudit_20261009` (private Drive folder ID `1cuydHKdWayl_3Ge0aah4NKrVlhjTudIO`). Contains mask location/color overlays, two experimental geometric SVG/PNG pairs, manifest with hashes. Tests `tests/test_accessory_goggles_clothing_audit.py` and related research suite **40 PASS**.
