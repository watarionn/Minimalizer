# Lane A L02: signed H06 class7/background owner leakage (2026-10-25)

**Known-character source-only research. Candidate REJECTED. No P0/P1 improvement accepted. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Verified evidence and frozen-proposal protocol

Canonical private source is the existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. Signed reviewed-source ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, frozen Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, class32 source observer ZIP `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg ZIP `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`, and independent DeepFashion2 ZIP `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04` were fetched from their existing canonical Drive locations. Source SHA from embedded RGB/alpha matched the signed review audit. Internal reviewed/Run30/AnimeSeg manifests matched 19/7/5 members; independent DeepFashion2 prediction array SHA matched the archived source-free metrics.

The source-only candidates were frozen to SHA-256 **before** opening human postscore masks. The exposed H06/H08 characters are not unknown-character holdouts. No annotation coordinates or human masks were inference inputs.

## P0 negative result: RGB proximity is insufficient for class7

A research-only near-core color-gap hypothesis admitted SegFormer class0 or class7 (class7 only with AnimeSeg generic clothes), source alpha, LAB proximity to existing frozen class5/10 garment core, <=12px proximity and >=128px connected islands. It preserved original owner, 4/8 component identity and source alpha. This code was **not** integrated or approved.

- H06 composed baseline: TP **294,020**, known FP **1,077**, known FN **20,803**, known-only IoU **0.930738**.
- H06 trial: **12,955 added source pixels**, of which **4,185 model class0** and **8,770 model class7**. Postscore TP **296,940** (+2,920), known FP **1,077** (unchanged), FN **17,883**, known-only IoU **0.939981**. **10,035 added pixels remain human-unlabelled/unknown**, not negatives. Only **1/12,955** added pixels overlaps the independently pinned garment-specific DeepFashion2 observer. Source-only visual inspection showed substantial additions on visible blue trousers. **REJECT** despite improved exposed known-only IoU.
- H08 trial: **192 class0 additions**, TP and known FP unchanged; **192 unknown**. DeepFashion2 support 174. No demonstrated P0 gain; **REJECT**.
- A separate conservative neutral class32 island-abstention hypothesis accepted no changes on either signed case because of frozen 4/8 topology and core-fragment retention. **REJECT as no-op**.

These are **not** unseen generalization results, and a higher known-only IoU does not justify drawing unknown trouser pixels as coat. Model class7 pants, class25 bag and class0 background need independently authenticated garment-specific evidence before semantic owner promotion. Generic AnimeSeg `clothes` does not establish outerwear ownership.

## Source-free guard staged for review

`tools/research/local_l02_high_risk_taxonomy_promotion_gate.py` checks aggregate source-only model-class additions, independent garment-specific support and unknown coverage, without loading images or masks. For H06 it returns `MODEL_CLASS_0_7_25_UNSUPPORTED`, lower bound **12,954 unsupported high-risk additions**. Twelve focused negative tests passed locally. Even when the risk veto is clear, the gate never declares Phase4, unknown generalization or Golden PASS.

The new gate is dormant and does not modify image inference, production LocalWorker, B L04/L07, Public/C08, Golden or user acceptance. GitHub full CI and unseen signed blind evaluation remain unverified. H04/H06/H08 P0 cases remain unresolved (3); **new accepted P0 improvements 0, P1 improvements 0**. H06 remaining best-known FN **20,803**, known underlayer FP **1,077**; H08 previously merged research best-known FN **12,349**, arm FP **17**; H04 known FP **4,423**. Existing PR #433's +849 H08 partial improvement is not recounted.
