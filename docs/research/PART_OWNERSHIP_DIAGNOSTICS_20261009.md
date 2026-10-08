# Part Ownership Diagnostics (2026-10-09)

**Completed empirical diagnostic, source-mask comparison, not visual Golden PASS.** Existing GC001 research-only character vector scene `HairTonalOwnershipScene_20261009/part_owned_tonal_hair_scene.svg` was decomposed by original SVG `data-part` into separate, transparent SVG and 340px rendered PNGs. Each alpha mask was compared to the saved Phase04 original source part mask. Do not interpret any single isolated layer's coverage as final composited visibility or color correctness.

| Part | Source pixels | Isolated SVG paths | Covered | Missing | Excess | Coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| face | 4808 | 0 | 0 | 4808 | 0 | 0% |
| hair | 14654 | 8 | 14605 | 49 | 397 | 99.666% |
| accessory_or_held_object | 217 | 1 | 15 | 202 | 0 | 6.912% |
| major_clothing | 3737 | 5 | 3051 | 686 | 30 | 81.643% |
| torso | 5827 | 3 | 5382 | 445 | 54 | 92.363% |
| neck | 1996 | 2 | 1872 | 124 | 17 | 93.788% |
| left_arm | 2717 | 3 | 2490 | 227 | 22 | 91.645% |
| right_arm | 5923 | 3 | 5649 | 274 | 39 | 95.374% |
| lower_body | 12563 | 3 | 10492 | 2071 | 12 | 83.515% |

**Critical scope safeguards:** The Phase04 `accessory_or_held_object` mask has only 217 pixels, so it is NOT a reliable complete ground truth for **goggles as a whole**. The 202/217 missing pixels are a concrete deficit for that *specific* mask, not proof that 93% of entire goggles are absent. Similarly hair has 397 isolated SVG pixels outside the original hair mask because corrected inter-eye forelock geometry extends into the originally misclassified face region; do not treat all 397 as hallucinated. The official source masks were found pairwise disjoint in this diagnostic. The 4808 missing face pixels are intentional after the false skin-plate removal and cannot be fixed by painting a face ellipse.

Source-only diagnostic code `tools/research/part_ownership_diagnostics.py`; target-based tests `tests/test_part_ownership_diagnostics.py` plus established preceding research tests: **38 PASS**.

Evidence: `chatGPT及びCodex用/Minimalizer/PartOwnershipDiagnostics_20261009/`, Drive folder ID `18p44Ake0-Tj16lq4m8Q4C89muPFoL20i`. It includes each part's isolated SVG/PNG pair, `part_isolation_grid.png`, and `manifest.json` with mask/alpha/source overlap and file SHA-256.

Next implement **Source-Observed Accessory + Clothing Reconstruction Gate**: first inspect the tiny accessory mask's actual coordinates and source colors, then classify goggles independently (source-observed, no invented 3D accessory); compare isolated role coverage, original silhouette and 2+ Golden cases. For clothing target both coverage and palette region preservation; do not paint giant navy slabs. Face separately requires observationally grounded skin/color boundary without full hidden-skin invention. Research only; no Local/Public deployment.