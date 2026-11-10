# Lane A L02: H06 bag-occlusion false-positive in independent outerwear overlap (2026-10-25)

**Research-only signed known-case negative. New accepted P0/P1 improvement: 0/0. Known H04/H06/H08 P0 cases unresolved: 3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Authenticated inputs and source-only proposal

Read the existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`, not a newly invented folder. Reverified the canonical ZIP SHA-256:

- Reviewed H04/H06/H08 evidence: `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; internal manifest **19/19**.
- Frozen Run30 owner: `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; manifest **7/7**.
- SegFormer source-only class observation: `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`.
- Independent DeepFashion2 garment observer: `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`.
- Embedded H06 signed WebP source: `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.

An exploratory **source-only** candidate intersected unowned source-alpha SegFormer **class25 (bag)** with the independent DeepFashion2 outerwear-positive mask. It produced **6,586 original-source pixels in one 8-connected component**, directly touching **174** frozen class10 coat-core pixels. Run30 coat owner component counts stayed **9→9 (4-neighbour)** and **8→8 (8-neighbour)**. No generated pixels or hand-mask inference inputs were used. This is an exposed known H06 hypothesis, **not** an unseen or frozen-before-human-review benchmark.

## Why the apparently large score gain is invalid

Postscore against the *existing* coarse reviewed outerwear mask labels all **6,586** candidate pixels as positive outerwear (0 explicit negatives, 0 unreviewed). A numerical-only gate would therefore claim a major coat recovery. **Private original-RGB visual inspection instead shows the candidate covers the visible patterned handbag/accessory in front of the tan coat.** The coarse outerwear review polygon overlaps this occluding bag. The independent outerwear observer also incorrectly supports it. Thus model agreement and reviewed-mask overlap do **not** establish coat ownership here.

**REJECT the entire 6,586px candidate.** It is not an accepted P0 improvement; do not count these pixels as repaired coat, render them as coat, change Golden, or silently revise the signed human mask. The current H06 coat FN 20,803px is a historical reviewed-mask metric and must be annotated as potentially affected by accessory occlusion, not rewritten without a new authorized review.

H04 has zero independent outerwear-positive class25 additions in this check; H08 has zero. These are exposed negatives, not generalization evidence.

## Code repair and release boundaries

The existing source-free `local_l02_high_risk_taxonomy_promotion_gate.py` previously cleared its *risk-specific* veto when all class25 additions had verified same-pixel independent outerwear overlap. It still did not itself authorize production, but downstream use of `NOT_AUTHORIZED_BY_THIS_AUDIT` could wrongly treat the risk as resolved.

Now any nonzero class25 bag/accessory addition remains **HOLD**, even when independently supported 100%. New receipt field `class25_accessory_conflict_pixels` and reason `MODEL_CLASS_25_ACCESSORY_CONFLICT` identify this exact failure. Existing unsupported-risk reasons remain backward-compatible. Two negative regressions were added, including the **6,586px signed H06 source-only count**. Local mirror of the exact GitHub code blob `bb81f786debbc74a85aad44006d175166dd927a0` passed **21 focused tests**. Full repository CI, unknown signed blind, Phase4 and source-only complete H06 composed-frontier replay were **not** certified by this patch.

Only source-free A research gate, tests and this report change. The separate Draft PR #436 provisional underlayer remains unapproved, with **49 arm + 8 coat** contaminated pixels. Lane B L04/L07, Public/C08, production LocalWorker, Golden and user approval are untouched. Next meaningful P0 step is independently grounded sleeve/coat-vs-bag/skin separation and human re-review of the occluding accessory boundary; do not tune exposed IoU to turn bag pixels into coat.
