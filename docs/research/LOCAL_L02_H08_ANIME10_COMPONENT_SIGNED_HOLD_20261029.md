# L02 exposed H08 independent-clothes component shadow (2026-10-29)

**Research-only, not accepted P0/P1 or current-main quality approval.** This is an A-only source-free evidence note for PR #445. No original images, private masks, NPZ, human coordinates, or private comparison board are committed.

## Source and authority boundary

- The independently stored signed H06/H08 WebP source and Run30 owner archives were read from the existing non-shared Drive `chatGPT及びCodex用/Minimalizer` evidence hierarchy.
- Verified complete private ZIP SHA-256 pins: Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, reviewed human masks `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, class32 source-only observation `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, and AnimeSeg offline384 `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`.
- Original encoded H06/H08 SHA-256: `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` / `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`. Run30 frozen owner and class observations were used as historical exposed-case inputs, **not** reconstructed exact-main composed owners.
- The source-only candidate was computed and its owner SHA frozen before the separate human-mask postscore. AnimeSeg class10 is general clothing, not an outerwear oracle. The source-only wrapper does not itself authenticate upstream pins. The contact dominance threshold and component size were explored on known images; **no blind generalization is claimed**.

## Candidate and rejection

The initial all-class32 component contact candidate recovered 44,712 correct H08 garment pixels but also admitted **2,308 known arm pixels**, so it was **rejected** despite preserving source/owner topology after Voronoi partition. It is not a safe P0 improvement.

The narrower independent-AnimeSeg-class10 candidate adds only source-opaque class32 pixels to an already frozen owner. It uses dominant source-only component boundary contact, an 8-neighbor cross-owner exclusion, a 4-component Voronoi seam, and 4/8 connectivity pruning. It never erases or reassigns frozen owner pixels, never generates source pixels, and does not read labels for inference.

| Signed exposed case / reviewed-only score | Historical Run30 | Anime10 shadow | Difference |
| --- | ---: | ---: | ---: |
| H08 true garment owned | 96,535 | 115,320 | +18,785 |
| H08 garment FN | 60,035 | 41,250 | -18,785 |
| H08 known false owner | 0 | 0 | 0 |
| H08 known arm false owner | 0 | 0 | 0 |
| H08 newly owned unknown | 0 | 58 | +58 |
| H06 true garment owned | 291,088 | 291,088 | 0 |
| H06 known false owner | 11,551 | 11,551 | 0 |

H08 adds 18,843 pixels: 18,785 reviewed garment, 58 unknown, 0 reviewed known false. H08 output owner SHA-256 `bd8d5fdc2d23c4ce828333f997786c8d80418a8865ae972f5c4c5ad5afd9f2d4`; H06 unchanged owner SHA-256 `4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317`. Both preserve 4/8 original component identity, cross-owner contact additions 0, frozen owner erasures 0, and original-source opacity.

**Private visual review:** The right sleeve recovers a large visible region; the left sleeve remains conspicuously incomplete. H06 underlayer contamination is untouched. H04 was not re-evaluated. The H08 remaining FN 41,250 is still a major defect; a successful synthetic test or known-case pixel recovery is **not** a Phase4 PASS.

## Integration and preservation

- New dormant A-only source-free module: `tools/research/local_l02_anime_clothes_component_shadow.py`.
- New negative-control tests: `tests/test_local_l02_anime_clothes_component_shadow.py`. Isolated source-free 5/5 PASS, not exact PR-head full CI.
- No production inference wiring, B L04/L07, Public/C08, LocalWorker or Golden edits.
- Private candidate arrays, comparison board and signed private member manifest were assembled in a local temporary ZIP, SHA-256 `50d8d74225cfc608dd5350960ecccf10065457c341717753b3242e68151ef2bb`. Upload to the existing non-shared Drive folder failed with `container_session_unavailable` twice; **do not claim cloud preservation**. Do not publish private evidence to GitHub.

## Remaining hard gates

Accepted P0 **0**, accepted P1 **0**. H04/H06/H08 major defects unresolved **3**. H08 remains a known-case research improvement only; H06 frozen class32 underlayer FP needs an independent positive semantic correction, not additive sleeve recovery. H04 regression, exact-main composed-owner lineage, independently pinned full source/observer input, source-only Phase4 critical-part/semantic ownership and 4/8 topology, genuinely unseen signed blind cohort, full PR CI, Golden approval and physical iPhone acceptance are still required.

**L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Keep PR #445 Draft; do not merge or activate this shadow.
