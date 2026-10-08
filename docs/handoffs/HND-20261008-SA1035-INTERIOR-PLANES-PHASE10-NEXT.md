# HND-20261008 SA10.35 Phase9 → Phase10: interior semantic color-plane refinement

**Current state:** Phase9 research implementation COMPLETE, quality-sensitive deployment **NO-GO**.
Repo `watarionn/Minimalizer` · branch `research/sa1032-svg-contour-proposals` · **draft PR #223, do not merge/deploy**.
Report: `docs/zerobase/SA10_35_PHASE9_INTERIOR_COLOR_PLANES_20261008.md`.

## User visual direction

User considers the **outer silhouette strong** and wants to improve **inner color regions**. Keep the exact Phase8 adaptive outer geometry immutable while exploring cleaner, more meaningful color areas in hair, apparel and accessories. No source-texture copying, generative pixels, face-feature drawing, or ungrounded detail invention. A smaller LAB color error is not equivalent to aesthetically better minimalization.

## What was actually run

- Two SHA-distinct original inputs, GC001 and Juufuutei-Raden.
- Source Stage04 owner mask checksum verification, Phase8 adaptive vector checksum verification and pixel-exact reproduction of saved Phase8 adaptive preview, unchanged original 11 outer primitives.
- Source-observed RGB medoid, deterministic 2-centroid LAB contrast, 5–30% eligible owner footprint area, >=120 px, 1 polygon per owner, <=28 vertices and <=3 extra subplanes per image.
- Face, both arms, unbound unknown, neck excluded; overlays clipped to parent and protected masks, no exterior silhouette modifications.
- GC001 source LAB MSE on eligible owner pixels **improved 8.8819%**, 3 new color planes (torso/hair/major_clothing), 28 total added vertices.
- Raden source LAB MSE **improved 19.0316%**, 1 new hair plane, 12 vertices.
- Source-to-research silhouette remains Phase8 adaptive: GC001 IoU .9982763313072667, Raden .9995681651336529; **raw topology PASS**.
- Visual side-by-side, original compatible baseline and output PNG plus proposal JSON and metrics on Google Drive:
  `chatGPT及びCodex用/Minimalizer/SA1035_Interior_Color_Planes_20261008/`
  https://drive.google.com/drive/folders/15vF3SShOJiVymXGPSxe55MoEGYR9Rpps
- Machine-readable `docs/zerobase/evidence/sa1035_*.json`, deterministic rerun with matching hashes in both cases.
- 69-test extended regression, focused GitHub Actions gate in `.github/workflows/sa1032-svg-research.yml`.

## Current design

`minimalizer_zerobase/reviewed_sa10/interior_color_planes.py`
`tools/run_sa1035_interior_color.py`
`tools/run_sa1035_interior_crosscase.py`
`tests/zerobase/test_sa1035_*.py`

Source palette sample is a real observed pixel (not LAB centroid invented). Geometry is polygonal and clipped, only inside existing owner's Stage8 rendered mask, no owner/material rewriting. Extra painted geometry **must** count: GC001 11 existing + 3 interior = 14 total geometric shapes; Raden 11+1 =12. Current screenshot may still have misplaced color blocks; human review pending.

## Real blockers

1. Phase8 existing **outer vector ring vertex cap is still FAIL**: GC001 3,604 >1,887, Raden 2,370 >1,412. New interior subpaths increase geometric complexity, not automatically admissible.
2. **SVG browser clip parity** missing for parent source owner + protected face/arms. OpenCV clipped raster is insufficient evidence.
3. **Human visual review** not completed. Broad light source color areas can be semantically wrong. The first attempt produced an oversized GC001 pale lower-body wedge and was rejected by tighter 30%-area protection.
4. Extra anatomy/garment identity: seek a clear tie, collar and garment-color hierarchy without bloating the tie, changing arm color or drawing facial features.
5. Multi-image design generalization beyond 2 sources still pending.

## Recommended next engineering phase

- Freeze outer masks, ownership and pixel colors as verified baseline; do not revisit silhouette unless separate strict source topology gate calls for it.
- Formalize `interior_plane` within owner as source-observed 1–2 clean Bézier/low-vertex material fields, score them on *both* source LAB fit and region readability/vertex complexity. Add adjacency and protected-color-family controls so e.g. outfit white isn't interpreted as transparent background or a new skin patch.
- Implement deterministic **browser-backed SVG clipping parity test** against the exact raster preview with external silhouette frozen; preserve singleton/degenerate holes and arm protection.
- Require SVG browser parity, original outer **and combined inner geometry budgets**, all original hard gates, independent real-case tests and human signoff before promotion.
- Keep GitHub canonical, Drive binaries under `chatGPT及びCodex用/Minimalizer`. Use RDC only for actual local source/test images and Drive mount file persistence.
