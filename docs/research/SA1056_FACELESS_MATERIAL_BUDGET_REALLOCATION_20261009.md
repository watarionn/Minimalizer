# SA10.56: Reallocate faceless SVG vertex savings to real source-observed hair and garments

2026-10-09 · **Signed two-case research PASS** for existing deployed SVG budgets and color MAE. Human visual Golden **HOLD**, original source Stage8 ring budget **FAIL**, canonical production **UNCHANGED**.

## Purpose, source policy, and what this does not do

The accepted standard style is faceless (`docs/TARGET_STYLE.md`, face primitives off by default). SA10.55 established a SHA-locked faceless research SVG and removed all visible source face-feature paths while retaining one original Stage04 face-mask guard, skin color, and genuine source-owner geometry. This released **103 vertices on Raden** (1,412 → 1,309) and **172 on GC001** (1,882 → 1,710), giving total budget headroom **103** and **177** respectively. SA10.56 spends only source-evidenced vertices on hair, major clothing, torso, lower body. It does **not** reintroduce eyes, nose, mouth, eyebrows or synthetic skin slabs.

Inputs are private, SHA-verified Raden signed source set (7 files) and GC001 (8 files), and **exact SA10.55 final research SVG hashes**: Raden `fd65000ad4e814348f1158871e9e049b74fffbf7d84e4b4f25c35ee375d2d88a`; GC001 `ca077a2df9d134926a4c433746398dd5f9d3dc79818ded611fac32f9623e859b`. Chromium v144.0.7559.96 DPR1 draws every candidate at original 340×340 size, and actual source RGB from these signed original images is the comparison authority. Original photo background is not compared against intentionally neutral SVG background.

## Implementation and admission conditions

`tools/research/sa1056_faceless_material_reallocation.py` generates deterministic source LAB k-means 3-cluster proposals inside each authentic source-owner visible region (`hair`, `major_clothing`, `torso`, `lower_body`). Source color for each contour must be a medoid that **exists verbatim in that exact original RGB owner region**. Connected-component polygons use OpenCV closed contours, area >=20 or >=45, `approxPolyDP` epsilon 2.5, 4, 6, or 8, and retained source owner masks. Every candidate is inserted inside the corresponding **existing masked owner SVG group**. No new mask references, Stage9/37 source polygon changes, owner-order changes, invented components, raster embeds or source image generation are allowed. Every new SVG path vertex counts against the strict full expanded budget, not merely XML length. Policy default hair-first prioritizes visible head identity.

A candidate **must** (1) fit the true SVG limit, (2) improve both original source visible-character RGB MAE and its source material owner RGB MAE, (3) preserve every pixel of the original signed faceless face, both signed arms and everything outside source-visible body, as verified by real Chromium pixel equality, and (4) preserve original signed masks, Stage9/37 colors, existing face guard and canonical `data-minimalizer-face-features=off` audit. One candidate per material is chosen based on the lowest real composite source MAE among feasible options; non-improving candidates are rejected. The modified SVG is research-only.

## Verified real Chromium measurements

| Metric | Raden SA10.55 | Raden SA10.56 | GC001 SA10.55 | GC001 SA10.56 |
| --- | ---: | ---: | ---: | ---: |
| **Expanded SVG vertex occurrences** | 1,309 | **1,409** | 1,710 | **1,873** |
| Strict budget | 1,412 | **PASS (+3 room)** | 1,887 | **PASS (+14 room)** |
| Source-visible foreground RGB MAE (lower is better) | 28.880513 | **26.120754** | 47.031444 | **41.913533** |
| Existing face microfeatures in standard output | 0 | **0** | 0 | **0** |
| Changed pixels of face, protected left/right arms, outside visible source | 0 | **0** | 0 | **0** |

All four source-owned material regions accepted an independent source-improving color contour in each image, using these **true charged vertices**: Raden hair 48 / clothing 43 / torso 6 / lower body 3 = **100**; GC001 hair 56 / clothing 29 / torso 25 / lower body 53 = **163**. The actual old Source Stage8 ring budget is a different metric and is **NOT resolved** by passing the deployed budget.

Original-pixel medoids actually painted: Raden hair RGB(202,190,184), clothing RGB(77,80,77), torso RGB(205,191,185), lower body RGB(66,65,68); GC001 hair RGB(250,242,247), clothing RGB(245,245,255), torso RGB(49,48,45), lower body RGB(237,242,250). The artifact-side privacy-safe JSON includes per-material cost/accuracy and source SHA provenance but no traced contour coordinates or raw source photos.

## Visual result, limitations, reproducibility

The original-inclusive comparison board `sa1056_two_case_material_board.png` shows real signed original / SA10.55 faceless / SA10.56 source-material proposal side by side for both characters. Raden gains a source-derived light hair plane, muted clothing interior and small torso/lower-body details. GC001 gains white hair/garment regions and dark clothing planes. **Important:** facial features are intentionally suppressed, and the simplified hair/wearable/macro silhouette is visibly still too coarse for full identity Golden. Lower source RGB MAE does not establish correct semantic garment parts, topology or acceptable artistic style. There is no human approval, and no production routing change.

- Regression `tests/zerobase/test_sa1056_faceless_material_reallocation.py`: **9/9 PASS** with both private signed origins and exact SA10.55 candidate SVG pins. Covers signed source/SVG hash tampering, medoid provenance, strict expanded path accounting, faceless fail-closed input, source/output isolation, full Chrome composited arm/face/background pixel protection and two-budget caps.
- Two separate complete Chromium research evaluations generated **8/8 identical output SHA-256** across 2×3 SVG/PNG, 1 review board and 1 metrics JSON. The stage report contains the individual artifact SHA-256 values; archive has an independent member manifest.
- Actual candidate SVG geometry, source-inclusive comparison board and authentic screenshot files belong **only** in approved private Google Drive under `chatGPT及びCodex用/Minimalizer/SA1056_SourceMaterialBudgetAllocation_20261009`. No original artwork/photo, candidate SVG path or original-containing image should enter GitHub. GitHub holds code, tests, this report and coordinate-free evaluation JSON only.
- No GPU, RDC, generated image, model update, production deployment or live-worker activity.

## Release gate / SA10.57

`SOURCE_AUTHORITY_PASS`; `SOURCE_PIXEL_PALETTE_PASS`; `TWO_CASE_FACIAL_MICROFEATURES_OFF_PASS`; `MASK_ARM_FACE_PIXEL_EXACT_PASS`; `TWO_CASE_TRUE_EXPANDED_VERTEX_CAP_PASS`; `REAL_CHROMIUM_VISIBLE_SOURCE_MAE_IMPROVED`; `SOURCE_STAGE8_RING_CAP_FAIL`; `IDENTITY_AND_HUMAN_GOLDEN_HOLD`; `PRODUCTION_UNCHANGED`.

**SA10.57 next:** prioritize silhouette, arm, hair-part occlusion and clothing-part adjacency/source-color boundary identity rather than accumulating weak image-detail polygons. Use independent source-visible part region silhouette/IOU and Chrome delta gates. Explicitly resolve pathological skin-color slabs if they occur (the prior Face Plate audit forbids them). Require human visual approval and Stage8 release policy closure before any promotion.

## Reproduction

```bash
python tools/research/sa1056_faceless_material_reallocation.py \
 --raden /private/signed/Raden --gc001 /private/signed/GC001 \
 --raden-svg /private/SA1055/raden_faceless.svg \
 --gc001-svg /private/SA1055/gc001_faceless.svg --out /private/SA1056
SA1056_RADEN_ROOT=/private/signed/Raden SA1056_GC001_ROOT=/private/signed/GC001 \
 SA1056_RADEN_BASE=/private/SA1055/raden_faceless.svg SA1056_GC001_BASE=/private/SA1055/gc001_faceless.svg \
 python -m pytest -q tests/zerobase/test_sa1056_faceless_material_reallocation.py
```
