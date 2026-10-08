# SA10.35 Phase 9: silhouette-locked interior color-plane research

Date: 2026-10-08 JST
Repository: `watarionn/Minimalizer`
Research PR: #223, DRAFT / unmerged

## Decision

**Interior color-plane proof of concept and reproducible two-image evaluation: COMPLETE.**
**Production deployment: NO-GO.** Existing outer-vector budgets are still exceeded, SVG browser/clip parity is not verified, and human visual approval is pending. A lower LAB color error is not evidence of polished minimalist art.

The user liked the silhouette and asked to improve interior colors. This phase **freezes the already-source-verified Phase8 adaptive outer polygons** and adds a small number of explicitly counted internal, source-observed color planes.

## Implemented

- Source RGB Lab region analysis from the **original input**, with verified input SHA and individual Stage04 owner mask hashes. No generative model, inpainting, filling source pixels, or copying source textures.
- Deterministic two-cluster Lab contrast for each eligible existing owner; geometric candidates are smoothed and fitted into **one closed polygon with <=28 vertices**, per eligible owner, from large contiguous source-observed regions.
- RGB choices are **real source-observed pixel colors** taken from the candidate's own polygon region. Not fabricated colors or bitmap overlays.
- Owner whitelist: `hair`, `torso`, `major_clothing`, `lower_body`. Face, both arms, neck, head support and unbound/unknown are excluded.
- Parent clipping plus explicit source-owned **face and both arm protected masks**. Paint each plane immediately after its parent primitive, preserving painter's order.
- Source-color candidate is accepted only when area is 5–30% of its owner and >=120 px, source Lab-MSE improves by >=7.5% on its owner, material differs meaningfully, and polygon has <=28 vertices. The maximum accepted subplanes per image is 3.
- Original 11 outer primitive IDs/owner/material order, polygon bytes, rendered mask, raw topology, source SHA, Stage04 owner-mask SHA and visible arm/face RGB remain untouched. Research pipeline verifies its reconstructed **outer-only preview is pixel-identical to the Phase8 saved preview**.
- **Every interior polygon is separately counted as an extra geometric SVG subpath.** Research result is not falsely described as still 11 total filled shapes.
- Face remains a simplified solid source-observed color (original face guard), **never draws new eyes/nose/mouth**.

## Two independent real-image tests

| Criterion | GC001 | Juufuutei-Raden |
|---|---|---|
| New interior color subplanes | 3 (torso, hair, major clothing) | 1 (hair) |
| Added polygon vertices | 28 | 12 |
| Existing outer primitives | 11, unchanged | 11, unchanged |
| Estimated total geometric elements | 14 | 12 |
| LAB source-color MSE improvement over eligible owner regions | **8.8819%** | **19.0316%** |
| Outer silhouette IoU (unchanged from Phase8 adaptive) | 0.9982763313 | 0.9995681651 |
| Unnormalized global topology gate | PASS | PASS |
| Face and both arm RGB byte-for-byte protected | PASS | PASS |
| Changes outside original drawn geometry | 0 | 0 |
| Changes outside recorded interior polygons | 0 | 0 |
| Saved adaptive preview bytes and pixel reproduction | PASS | PASS |
| Original Stage12 outer vertex budget | FAIL | FAIL |
| Browser-rendered SVG with parent/protected clipping | UNVERIFIED | UNVERIFIED |
| Human visual gate | PENDING | PENDING |

Source hashes are distinct; independent cross-case provenance coverage **PASS**. Re-running each evaluation separately produced identical SHA256 for three outputs per image: full metrics, source-plane proposal JSON and candidate PNG.

Initial research made an oversized gray/white lower-body region in GC001. An explicit 30%-of-owner maximum and 5% minimum prevented the blob and narrow ambiguous subplanes. The retained GC001 research candidate visibly places a small bright hair region (goggle area) and narrow garment highlights. This is **not** an independent human visual signoff.

The LAB metric measures only source-RGB color fit inside eligible owner regions, not subjective readability, necktie shape quality, broader recognition, or visual attractiveness. Extra colors can improve MSE but harm minimalism. This is why the SVG and human gates remain blocking.

## Code and verification

- `minimalizer_zerobase/reviewed_sa10/interior_color_planes.py`: deterministic source medoid color selection, clipped geometric proposals, owner/arm/face protected z-order rendering.
- `tools/run_sa1035_interior_color.py`: provenance-gated two-dimensional research preview, exact baseline reconstruction and color-error evidence.
- `tools/run_sa1035_interior_crosscase.py`: cross-source evidence coverage and strict promotion blockers.
- `tests/zerobase/test_sa1035_interior_color_planes.py`: geometry clipping, large-area/noise rejection, observed colors, excluded owners and determinism.
- `tests/zerobase/test_sa1035_interior_crosscase.py`: distinct source, arm protection, accounting for extra painted geometric paths, no promotion.
- Local extended regression **69 tests PASS** (prior 56 + 8 interior + 5 cross-case); research GitHub Actions workflow must PASS for branch-head verification.
- No production scene, worker, browser fallback or main local working tree modified.

## Preserved artifacts

Machine-readable:
- [GC001 owner color-plane evidence](evidence/sa1035_gc001_interior_planes_20261008.json)
- [Raden owner color-plane evidence](evidence/sa1035_raden_interior_planes_20261008.json)
- [Two-image interior gate](evidence/sa1035_two_case_interior_gate_20261008.json)

User-review visuals / research JSON:
[Google Drive `chatGPT及びCodex用/Minimalizer/SA1035_Interior_Color_Planes_20261008`](https://drive.google.com/drive/folders/15vF3SShOJiVymXGPSxe55MoEGYR9Rpps).
Subfolders GC001 and Raden each contain original-compatible baseline preview, altered preview, source/base/new 3-way comparison, proposal geometry and metrics.

## Explicit hard blockers / next phase

1. **Existing vector vertex cap FAIL** from Phase8; the new interior subpaths add geometry (GC001 +3, Raden +1) and must also be assessed in the global geometry budget, not counted as free.
2. **Browser SVG clip parity UNVERIFIED**. Clipping by a stored owner polygon and excluding protected face/arm pixels is currently a research raster operation. Do not claim a browser-valid SVG until tested with real browser raster at the same resolution.
3. Face/arm preservation and the silhouette gate do not guarantee correct **interior color semantics**. A precise necktie/collar or color transition can still be wrong; require explicit review.
4. Improve true geometric abstraction and clean broad apparel panels, with actual source region observations but without inventing material, painting source details, adding face features or changing owner/unknown provenance.
5. Test on additional independent real images and obtain user visual signoff before considering a merge or production deployment.

Phase9 research stage is finished with **color fit improvement and safety PASS**, overall **NO-GO for production**.
