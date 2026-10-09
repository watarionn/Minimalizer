# MinimalizerPublic signed-source compact plane study (2026-10-09)

**Two-real-source arm-only research PASS; whole-character production NO-GO and Golden HOLD.** Research extension of draft PR #324.

## New algorithm
One even-odd SVG clip path per original source-visible signed arm replaces 95–132 rectangle clip elements. The path uses exact oriented source pixel-cell edges, retaining holes and separated components. Color planes use original-image RGB samples only, with a single source-derived base color and greedy rectangular color overlays. Original face details are not painted, and no SVG raster <image> is embedded.

Research files: `tools/research/public_geometry_js/compact_signed_planes.mjs`, `compact_signed_planes.test.mjs`, `compact_joint_real.mjs`, `prepare_signed_source_alpha.py`. Original images and signed masks reside solely in private Drive `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008`.

## Both-arms combined shape budget
| Frozen original | 24 shapes RGB MAE | 40 shapes RGB MAE | 60 shapes RGB MAE | 80 shapes RGB MAE |
|---|---:|---:|---:|---:|
| GC001 | 38.461 | 33.575 | 30.071 | 28.075 |
| Raden | 15.412 | 13.673 | 12.631 | 11.914 |

At the 40-shape budget, GC001 and Raden both allocate 15 left-arm color planes, 21 right-arm color planes, two original-signed clipping paths and two original RGB undercoats. **40 is for TWO ARMS ONLY, not the entire person.**

Actual Chromium 144.0.7559.96, 1× and 4×: every one of the 16 paired-arm candidates (2 original cases x 4 budgets x 2 roles) has 0 alpha outside signed source-visible masks and 100% alpha coverage within original-source-visible masks. Source alpha zero pixels are excluded, including 3 GC001 right-arm and 74 Raden left-arm signed pixels. RGB MAE is measured only inside verified visible original RGB.

Regression: 3/3 signed topology/provenance/determinism tests PASS locally and on connected Node v26. Repeat generation of 16 SVGs has 16/16 identical SHA-256. Windows independently generated 40-shape GC001 left/right SVGs with identical SHA to the evaluator.

## Important hard gates
- Exact clip geometry still contains 310+286=596 vertices for GC001's two arms and 388+246=634 for Raden. One path does not mean one vertex.
- All 40 shapes are spent on arms, leaving none for hair, torso, clothing, accessories and outer silhouette. Original Stage8 source-ring total budget remains unresolved.
- Interiors still look rectilinear; source color MAE improvements do not establish art quality.
- No whole-character z-order, Safari/Firefox, human Golden or product regression PASS.
- No production code change, merge or deploy. Face features remain hidden.

**Next:** whole-character budget allocator and color-region improvement, then all-owner browser Golden and feature-flag validation. Keep signed source ownership and no generated fill.

Private current research outputs are preserved under `chatGPT及びCodex用/Minimalizer/PublicGeometryJS_SignedClip_20261009`, prefixed `compact_` to avoid overwriting prior artifacts. Reproduction ZIP `MinimalizerPublic_Compact_SignedPlanes_20261009.zip` contains full testing code, browser screenshots and 56 artifacts, excluding original private source image bytes.
