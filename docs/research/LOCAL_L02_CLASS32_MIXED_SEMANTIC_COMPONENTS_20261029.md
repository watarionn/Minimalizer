# L02 signed class32 mixed-component semantic audit (2026-10-29)

**Decision: FAIL / HOLD.** This is a new post-inference structural diagnosis, not a P0 fix, blind holdout, or quality approval. Source-free code and tests only; no private images, masks, owner pixels, annotation coordinates or NPZ committed.

## Provenance

- Main at start: `4a4348990084848c981811b414e6221411271f84`; Draft PR #445 before this addition: `24cd2a7c7cb878178ddc8390219decd963bde09f`.
- Authenticated nested non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/`. ReviewedEvidence ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, sleeve-class observation ZIP `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`. Member SHA manifests: reviewed 19/19, owner 7/7.
- Original embedded encoded source SHA-256 H04 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`, H06 `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`, H08 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.
- Source alpha clips historical independent model class32. The human-reviewed masks are read **only after inference** for this audit. Unknown is not a negative. These are already exposed cases, not exact-main composed owners or unseen transfer.

## New structural diagnosis

The two largest class32 source-alpha-clipped components of each signed case contain **both true garment and explicit known false class membership**. Component sizes and postscore overlap counts are identical under 4- and 8-connectivity for these two largest components.

| Case/component | class32 px | reviewed true garment | reviewed underlayer | reviewed arm | unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| H04 / 1 | 12,007 | 11,529 | 0 | 102 | 376 |
| H04 / 2 | 3,940 | 3,251 | 0 | 617 | 72 |
| H06 / 1 | 27,078 | 19,151 | 4,791 | 0 | 3,136 |
| H06 / 2 | 19,169 | 11,612 | 6,535 | 225 | 797 |
| H08 / 1 | 28,522 | 27,207 | 0 | 681 | 634 |
| H08 / 2 | 23,112 | 21,094 | 0 | 1,681 | 337 |

**H06:** These two components contain **all 11,326 known Run30 underlayer false owner pixels**, but also **30,763 true coat pixels**. Erasing either entire component destroys valid coat. This demonstrates that whole-component veto, class32-wide OR/AND or connectivity checks alone cannot solve the H06 P0. The later composed/strict stage's **1,077 residual FP is a different stage** and must not be conflated with historical Run30.

**H08:** The two large class32 components contain **48,301 true coat/sleeve pixels** but also **2,362 known arm pixels**. Whole-component admission would import arm; whole-component rejection would retain severe sleeve loss. H04 similarly mixes 14,780 true garment and 719 known arm pixels in its two largest components. The model's component ID is not a semantic owner label.

## Engineering gate and disposition

- New **postscore-only** helper `tools/research/local_l02_class32_semantic_overlap_postscore.py` and `tests/test_local_l02_class32_semantic_overlap_postscore.py`. Isolated 4 negative-control tests PASS. It outputs only component counts without coordinates or pixels, and cannot be imported as a semantic inference oracle.
- Next real repair needs independently licensed, source-only **pixel/subpart-level outerwear-vs-underlayer/skin evidence** with explicit ABSTAIN, frozen candidate SHA before opening reviewed masks, and preservation of the true garment above. No known-case tuning or hand-label leakage.
- Follow with H04/H06/H08 regression, frozen owner and cross-owner contact gates, exact-current-main Phase4 replay, independent unseen signed blind, owner-PC merge-readiness + L02 tests, Golden and iPhone owner acceptance.

**Accepted P0 improvements 0, P1 improvements 0; unresolved major defects H04/H06/H08 = 3.** This is a diagnosis and an evaluation-gate implementation, **not a pixel correction**. PR #445 remains Draft and unmerged. No B L04/L07, Public/C08, production LocalWorker or Golden changes. `L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO`.
