# SA10.57: Source-signed faceless structure, protected silhouette boundary and material contour search

2026-10-09. **Two-case geometry protection and small source-grounded material boundary refinement PASS; source Stage8 ring policy FAIL; full-character silhouette similarity / Golden and production HOLD.**

## Scope and explicit nonclaims

The frozen target style is **faceless**, per `docs/TARGET_STYLE.md`. SA10.56 had improved original-source hair, apparel, torso and lower-body colors by inserting source-pixel medoid polygons into existing source owner groups, within actual expanded SVG vertex limits. However, visual inspection still shows missing hair locks, rough costume shapes and silhouette distortions. This stage verifies the original signed part relationship/outer-boundary protections and tests small vertex-neutral corrections of already source-observed material polygons. It does **not** imply source-correct silhouette geometry, complete clothing semantic topology, or artistic identity approval.

## Source authority and method

- Raden: seven SHA-locked signed source files; GC001: eight SHA-locked signed source files. Each set includes genuine source RGB, Stage04 face/left-arm/right-arm masks and source contour evidence.
- Immutable SA10.56 candidate SVG SHA-256: Raden `18474c41978f257ebf605040de4cfe2c532f6cc5f171b69089d8f48d921d349d`, GC001 `858080f4a738f41cade641fa24bf6414726f2bc9ce1b364f02400d9e0f37ed7e`.
- Verify corresponding SHA-256 of baseline **real** 340×340 Chromium144 DPR1 PNGs before every optimization. Reject changed input, changed source screenshot, altered geometry count, invalid source location or accidental overwrite.
- Derive **nine source-visible owner regions** from the existing signed owner data. Independently audit zero overlap and record pairwise 3×3-mask adjacency, including contact boundaries of original source owner parts. These are source-role **observations**, not an invented correct semantic relationship. Do not reorder, reassign or rebuild any existing owner or source mask.
- Freeze **every Chromium RGB pixel** in the signed Stage04 face, both arms, background/outside source-visible foreground, signed outer silhouette's 2px source-mask perimeter band, and all one-pixel owner-interface contact pixels. This is deliberately stronger than merely checking XML and owner labels. It prevents changing external character outline, reintroducing facial features, or shifting already observed part contact boundaries during this stage. It does **not** repair source-to-SVG global contour mismatch: it holds that separately for review.
- Among the **existing SA10.56 source-observed hair/major_clothing/torso/lower_body SVG polygon vertices**, rank at most five vertices per role by grayscale signed-original Sobel gradient inside the editable source owner. For each, test four cardinal 1px movements in **real Chromium**. Keep only source-global foreground RGB MAE improvements AND original-owner MAE improvements AND nonregression at signed-original high-gradient material pixels. Require bitwise equality in every frozen pixel, unchanged source color medoids, source Stage9/37 owner polygons, signed masks, paint order, and exact current expanded geometry count. No added vertex, invented limb/face feature, generated fill, extra mask use or source image embedding.
- This is a research optimizer, not production routing or local-worker deployment. A lower RGB MAE is **not** a claim that an anatomically accurate arm, correct occlusion or silhouette shape has been reconstructed.

## Real signed Chromium results

| Measurement | Raden SA10.56 | Raden SA10.57 | GC001 SA10.56 | GC001 SA10.57 |
| --- | ---: | ---: | ---: | ---: |
| Full expanded SVG vertex occurrences | 1,409 | **1,409** | 1,873 | **1,873** |
| Hard expanded deployed budget | 1,412 | **PASS** | 1,887 | **PASS** |
| Original-source visible-character RGB MAE | 26.120754 | **25.948808** | 41.913533 | **41.743042** |
| Accepted material contour vertex shifts | 0 | **12** | 0 | **11** |
| Real Chromium candidates tried | 0 | **68** | 0 | **80** |
| Signed owner count / source-visible overlaps | 9 / 0 | **unchanged** | 9 / 0 | **unchanged** |
| Signed 2px outer silhouette band RGB changes | 0 | **0** | 0 | **0** |
| Signed material owner-interface RGB changes | 0 | **0** | 0 | **0** |
| Signed face and both arms RGB changes | 0 | **0** | 0 | **0** |

Source owner contact pairs observed: Raden **14**, GC001 **17**; source-visible owner overlaps are zero. Source-signed outer band checked 7,227 pixels Raden / 9,567 GC001; contact interface checked 1,984 / 2,832 pixels. Strict immutable mask+source role+paint inventory holds. The hair, costume and torso forms visibly remain simplified. Frozen boundary pixels means that this stage does **not** improve the full silhouette itself, only the safe internal source-colored polygon edges.

## Validation and preservation

- Private SHA-authority regression `tests/zerobase/test_sa1057_structure_boundary_guard.py`: **9/9 PASS**. Includes input SVG/source tamper rejection, signed face/arm/frozen region masking, non-overlapping signed owner adjacency, original-source edge candidate confinement, source color and mask inventory, source/output isolation, real Chromium 2-case geometry + accuracy + SVG audit, unknown-case rejection.
- Two fresh full Chromium evaluations produced **8/8 SHA-identical artifact files**, including actual private SVG/PNG for both characters, full signed-original comparison board, and source-coordinate-free JSON metrics. Browser version `144.0.7559.96`.
- Store private candidate SVGs and original-inclusive comparison only in `chatGPT及びCodex用/Minimalizer/SA1057_SignedPartBoundaryGuard_20261009` on the approved user's Drive, along with code/tests/report/manifest/ZIP. Public GitHub only code, tests, report and no-coordinate metrics.
- **Gate**: `SOURCE_AUTHORITY_PASS`, `TWO_CASE_TRUE_SVG_BUDGET_PASS`, `FACELESS_TARGET_PASS`, `PIXEL_EXACT_ARMS_FACE_OUTER_BOUNDARY_AND_CONTACT_PASS`, `SIGNED_SOURCE_COLOR_FIDELITY_SMALL_GAIN_PASS`, `SOURCE_STAGE8_RING_FAIL`, `FULL_SILHOUETTE_SOURCE_FIT_UNRESOLVED`, `VISUAL_GOLDEN_HOLD`, `PRODUCTION_UNCHANGED`.

## Next SA10.58

Resolve the **separate original Stage8 source ring vertex budget** and source-to-SVG silhouette discrepancy without conflating them with the already passing compact research-SVG count. Evaluate source outline, hair/hand/garment part contact discrepancy quantitatively and explore pixel-proven dead/occluded geometry, counting every expanded SVG vertex. Preserve faceless policy and signed original arms. If old Stage8 policy proves structurally incompatible with acceptable silhouette, propose a documented change request, never silently relax the cap. Then multi-image artistic Golden and actual approved production integration can follow, not before.

## Reproduce (private signed authority required)

```bash
python tools/research/sa1057_structure_boundary_guard.py \
 --raden /signed/Raden --gc001 /signed/GC001 \
 --raden-svg /signed/SA1056/raden_faceless_material.svg \
 --gc001-svg /signed/SA1056/gc001_faceless_material.svg --out /tmp/sa1057
SA1057_RADEN_ROOT=/signed/Raden SA1057_GC001_ROOT=/signed/GC001 \
 SA1057_RADEN_BASE=/signed/SA1056/raden_faceless_material.svg \
 SA1057_GC001_BASE=/signed/SA1056/gc001_faceless_material.svg \
 python -m pytest -q tests/zerobase/test_sa1057_structure_boundary_guard.py
```
