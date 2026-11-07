# L02 signed Run30 class-owner risk ledger (2026-10-27)

**Lane A research / HOLD.** This is a new independent **postscore of the historical Run30 frozen owners**, not a new inference candidate, current-main Phase4 replay, unknown-character generalization, or accepted visible P0/P1 repair. No private pixels, masks, coordinates, images, or NPZ are committed.

## Provenance and separation

- GitHub main checked before analysis: `4a4348990084848c981811b414e6221411271f84`. This document belongs only to Draft PR #445's `research/local-*` branch.
- Non-shared canonical Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`.
- ReviewedEvidence ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598` (19/19 manifest members matched).
- Run30 owner ZIP SHA-256 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c` (7/7 members matched).
- SleeveSemantic independent class observation ZIP SHA-256 `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`.
- Encoded signed source SHA-256: H04 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`; H06 `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`; H08 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.
- All three frozen owner 4-neighbour and 8-neighbour archives have identical **pixel arrays** (XOR 0 for each case). This does not imply equal component counts under the two connectivities.
- Run30 owner arrays and independent class-ID arrays were frozen prior to human-visible-mask scoring. Human labels were **evaluation only**. Unknown reviewed pixels were neither positives nor negatives.

## Meaningful P0 attribution (known reviewed pixels only)

| Case | Frozen owner reviewed TP | Known FP | Missing reviewed outerwear FN | Major source-only class attribution |
| --- | ---: | ---: | ---: | --- |
| H04 | 49,386 | 4,423 | 3,186 | Known FP: class5 **3,704**, class32 **719**. FN: class30 **1,872**, class0 **536**, class33 **445**. |
| H06 | 291,088 | 11,551 | 23,735 | **All 11,551 known FP are class32:** underlayer **11,326**, arm **225**. FN: class25 **9,913**, class0 **6,042**, class7 **4,203**, class30 **3,577**. **No FN is class32.** |
| H08 | 96,535 | 0 | 60,035 | FN: class32 **48,343**, class30 **5,308**, class0 **3,143**, class2 **2,287**. |

**Critical non-destructive decision:** H06's existing class32 owner has **31,074 reviewed true outerwear pixels**, **11,551 known false-owner pixels**, and **3,988 unknown pixels**. Blanket class32 erasure would sacrifice at least **31,074 known true garment pixels**, even though all known H06 FP happen to be class32. A class32-only *addition* algorithm such as PR #445 cannot repair H06's existing underlayer/arm FP, nor H06's class25/0/7/30 missing garment. The class32 semantics are mixed, so a single class-ID OR/AND or label-informed threshold is not an acceptable repair.

H04 has a different dominant error: **3,704/4,423 known FP** already belong to class5, not class32. H04's existing class5 owner also includes **34,581 reviewed true outerwear pixels**. Blanket class5 veto is therefore destructive. H08's largest missing garment is class32 (**48,343/60,035 reviewed FN**) but the known glove/arm contamination documented separately means raw class32 promotion is unsafe.

## Engineering consequence, not a quality PASS

1. Prioritize **independent semantic discrimination** of H06 class32 coat versus underlayer/arm, while preserving its 31,074 known garment positives; separately address H06 class25/0/7/30 missing garment. Human labels must not enter inference.
2. For H08, retain a source-only independent glove/arm veto and both 4/8 frozen-component identities before allowing any class32 sleeve growth. Do not tune thresholds against exposed H08 and call it blind.
3. For H04, focus on class5 false ownership and class30 missing garment, not repeated class32-only tests. Existing true-owner pixels must remain protected.
4. Rebuild and authenticate **latest-main-derived** composed H04/H06/H08 owners before evaluating any proposed PR #445 changes. Historical Run30 statistics cannot be compared as if they were current-main improvements.

**Accepted P0 repairs 0, accepted P1 repairs 0; unresolved H04/H06/H08 = 3.** No new quality candidate, owner mutation, code merge, production activation, or Golden acceptance is authorized by this ledger. Still required: exact-main dependency closure, signed full replay, Phase4 exclusive semantic owner/connection/critical-part PASS, H04/H06/H08 regressions, unseen signed blind, full CI, Golden and physical iPhone owner acceptance. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No B L04/L07, Public/C08, LocalWorker production, or Golden files were changed.
