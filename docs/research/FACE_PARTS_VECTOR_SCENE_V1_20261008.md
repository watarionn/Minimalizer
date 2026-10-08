# Face Parts Vector Scene v1 (2026-10-08)

**Result: real complete vector SVG produced, geometry feasibility PASS, artistic quality NO-GO. No production rollout.**

The user wants face parts handled structurally without face-shaped painted overlays, and eventually a coherent whole-character SVG. This PoC reuses the exact GC001 340×340 original and stored source-aligned Phase03/04 body, hair, arms, clothes and accessory masks. Face-part observations from Face Parts Only v1 remain audit-only. Eyebrows are not verified and no eye/nose/mouth/eyebrow paths are created.

## Engineering outcome

- A *single* subject silhouette vector is constructed from the source mask, with underlay RGB chosen from original skin pixels. Hair, clothing, neck, arms and other source-owned geometric color parts are then layered from their original masks. There is **no independent face polygon, no post-processed face layer, no inpainting, no embedded raster**.
- Source color medoids only; each per-part palette is capped, and significant observed color components are independently vectorized. This results in a **genuine self-contained vector SVG with colored subject and background**, unlike PR #251's transparent line-only SVG.
- Actual GC001 output metrics: **27 SVG path elements / 290 vector contours / 5,489 vertices**. Original subject mask versus rasterized SVG alpha: **IoU 0.97584**, with **186 foreground false-positive pixels** and **1,134 missing subject pixels**. The mask still requires boundary topology correction.
- Comparison image SHA-256: `baade62648dd0e311c7cbd010ac58e14cbb6a14edfae11f83bd292b5ecce6c46`.
- SVG alpha is separately exported without a background; no false silhouette metric derived from a fully opaque background.
- **Visual review: NO-GO**. Despite the geometric progress, most hair appears nearly white rather than the source orange, the clothing has fragmented black and multicolored regions, and the blank face still reads unnaturally. The fixed research script preserves hair crossing face masks, but this does not fix overall hair color loss in the first result. *Do not assert good style/identity preservation.* The SVG's 27 path elements still contain hundreds of contours and thousands of vertices; it has not achieved true efficient geometric minimization.

## Provenance and files

Code: `tools/research/face_parts_vector_scene_v1.py`; offline tests: `tests/test_face_parts_vector_scene_v1.py` (**13 PASS including earlier SVG/Face Parts tests**).

Outputs in `chatGPT及びCodex用/Minimalizer/FaceParts_VectorScene_v1_20261008/`, Google Drive folder `10gCcK65qlo9uEMufkiEm-0PpfzSCIGMu`:
`character_part_vector.svg`, `character_foreground_alpha.svg`, `character_part_vector.png`, `character_foreground_alpha.png`, `comparison_source_vs_vector.png`, and `manifest.json`.
Source and each output SHA-256 are in the manifest; existing GC001 original verified at load. Remote cloud synchronization must be separately checked.

## Next gate

1. Audit **part-layer priorities and unowned pixels**, beginning with orange hair, goggles and navy/white uniform. Parts overlap and source RGB clustering cannot simply assume each per-mask cluster belongs entirely to the part. Explicitly verify RGB/palette-role gates before rendering.
2. Improve contours without violating the subject silhouette or arm/torso negative space; recover missing source 1,134 pixels via *source-matched geometry correction only*, not invented anatomy.
3. Independent face-feature omission must operate on true vector layers, not covering facial portions after the fact. Never return to a face ellipse. Brow observer remains unverified.
4. Require second-character tests and existing Semantic Golden before Local PWA integration; Public not modified.
