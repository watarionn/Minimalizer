# Kyoko Manual Reference v1 | adopted human-made reference

**Reference ID:** `KYOKO_MANUAL_REFERENCE_V1`  
**Official reference status:** `ADOPTED_MANUAL_REFERENCE`  
**Adopted by:** explicit user instruction, 2026-10-15  
**Coverage:** Hyakutou Kyoko face and upper-body crop only, 340 × 340 pixels. This is a **partial manual visual reference**, not full-body Golden ground truth.

## Canonical artifacts and access control

- **PRIVATE canonical Drive archive:** `chatGPT及びCodex用/Minimalizer/Kyoko_Manual_Reference_v1_PRIVATE_20261015.zip`.
- SHA-256 of ZIP: `63fd3a8b9b730ad641916b5daf14c8d149c508ac5a29aec2e2ac5c502e129db4`.
- Original supplied project JSON: `4c326494f7199e41607b86e4ac2985c61b9cd49f375ed7dc06236fcab2598b4c`.
- Original supplied trace SVG: `6274c1dda1bd8d3ddfdff091c1c3d4edb10b246890811cb0cc4f42783f35858e`.
- The original user files are preserved **byte-for-byte** in the archive, plus extracted underlay PNG, derived SVG-rendered preview, side-by-side view, and structural verification report.
- Do **not** copy JSON, SVG coordinates, original/source images, or review previews to public GitHub or public sites. The project JSON embeds the source raster in a data URL. The SVG does not embed the raster, but reveals manually traced coordinates.
- Drive uploaded and downloaded again: archive SHA-256 **matched** locally (747543 bytes).

## Evidence and provenance

- Generated with standalone `Reference Shape Editor` v1, schema `reference-shape-editor/v1`.
- 33 polygons, 172 distinct vertices, **54 shared vertices**, 0 invalid/self-intersecting polygons, all 33 SVG polygons agree with JSON; no raster embedding in SVG.
- The *underlay embedded in the project JSON* has PNG SHA-256 `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`.
- The historical signed C08 GC001 PNG has SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e` (as recorded in C08 Run141 checkpoint). **They are not byte-identical**. The relationship, crop transform, and pixel registration are **not verified**. Do not claim this is the signed GC001 image or use manual polygons as pixel-level labels of that signed source.
- Palette has `imported=false`, so colors are hand-selected/local Editor palette options, **not** verified as exact output of a canonical Minimalizer ColorStrip extraction.

## Allowed use

This user-curated human reference is an **official manually authored example** for human-intended polygon silhouette, hair/shoulder/arm separation and occlusion, garment color regions, layer sequencing, and manual Golden comparison preparation. A specific lesson from user C04 review: the character's **anatomical right shoulder/right arm**, located on **viewer-left** of a frontal portrait, must remain perceptually visible rather than appearing replaced by an oversized hair mass. This reference documents a human-preferred depiction; it does **not** prove source-mask truth.

For reproducible experiments, calculate candidate differences against **this reference and its own embedded underlay**, with explicit labels and content SHA. Compare to signed GC001 only after verified registration/matching source lineage, not by assuming shared 340 × 340 dimensions. Independently verify silhouettes, color ownership, actual rendered DPR1/2 and strict source-only provenance. A new user-edited reference requires a version **v2** rather than overwriting v1.

## Boundaries unchanged

- Never overwrite the signed original, official SA10.41, historical owner masks or original Stage8 source budget.
- No image generation, generative fill/inpainting or inferred content completion in Minimalizer output; default face microfeatures OFF.
- This adoption does not sign a Golden A/B judgement or approve revised Stage8 budget, Approved18/78, production deployment or iPhone acceptance.
- The release tracker must remain `ACTIVE_RELEASE_HOLD` (`C02 ABSTAIN`, `C03 HOLD`, `C04 HOLD`, `C05 NO-GO`) until independently satisfied.
- Scheduled C08 campaign remains paused; registering a reference does not restart it.

## Validation recipe

The public source-only validator accepts private paths without exporting any pixels:

```sh
python tools/references/verify_reference_shape_editor_export.py \
  '/PRIVATE/百灯キョーコ_見本_顔・上半身_trace.json' \
  '/PRIVATE/百灯キョーコ_見本_顔・上半身_trace.svg'
python -m unittest discover -s tools/references -p 'test_verify_reference_shape_editor_export.py' -v
```

The validator requires coordinate/shape/color consistency and rejects non-polygon SVG elements or malformed private image data. Its fixture-only tests do not contain original image bytes.
