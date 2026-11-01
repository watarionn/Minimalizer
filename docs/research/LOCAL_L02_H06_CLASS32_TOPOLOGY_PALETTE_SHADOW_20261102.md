# Lane A L02: H06 class32 topology-preserving color-competitor shadow (2026-11-02)

**RESEARCH ONLY, NOT QUALITY ADMISSION. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Goal and method

The signed H06 Run30 coat owner contains both genuine beige garment and white underlayer/cuffs in connected class32 sleeve regions. Whole-component veto and unconditional DeepFashion2 intersection remove large amounts of genuine coat. This new source-only research function uses the signed original RGB/alpha, its exact SHA-256, frozen SegFormer class IDs, and frozen Run30 exclusive owner. It uses class2 as a *color competitor*, not a ground-truth negative. Class5/10 garment and class2 competitor source-color medians must have adequate CIELAB separation; eligible class32 owner pixels are abstained only when competitor-like and local 4-connected owner topology is preserved. Full per-owner component counts are checked before returning. No human masks or coordinates are accepted as inference inputs.

**Known-case caveat:** this method and its fixed constants were developed while examining H04/H06/H08. Its known-character postscore is NOT an independent blind or unknown-character generalization PASS. The reviewed human masks were read only after the source-only candidate had been frozen.

## Signed H04/H06/H08 historical Run30 replay

Canonical private evidence was downloaded from the existing non-shared Drive folder, with four full ZIP SHA-256 pins verified: ReviewedEvidence 6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598; Run30 6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c; SleeveSemantic a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7; DeepFashion2 fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04 (provenance comparator, not candidate input). No private source, mask or annotation is committed.

| Case | Known FP before to after | Genuine coat TP before to after | Known FN before to after | Owner 4-components | Result |
| --- | ---: | ---: | ---: | --- | --- |
| H04 | 4,423 to 4,423 | 49,386 to 49,386 | 3,186 to 3,186 | jacket 5 to 5 | ABSTAIN |
| H06 | **11,551 to 1,944** | **291,088 to 290,794** | **23,735 to 24,029** | coat 9 to 9 | **Partial known-case shadow improvement** |
| H08 | 0 to 0 | 96,535 to 96,535 | 60,035 to 60,035 | jacket 29 to 29, coat 14 to 14 | ABSTAIN |

H06 abstained 10,176 pixels: 9,607 reviewed known non-outerwear, 294 genuine garment, and 275 unknown (not negatives). Labelled-only IoU 0.891885 to 0.918006 is **known-character diagnostic only**. Private visual comparison confirms major removals at white cuffs/underlayer, but final whole-character quality remains FAIL.

## Why this is not merged or promoted

The 294 correct garment pixels lost and any frozen-owner erasure violate the existing PR #445 no-erasure promotion postcondition. This is an isolated A-only candidate, not a drop-in owner patch. It requires a separate reviewed owner-transition contract, exact PR-head full QA, source-only critical-part/occlusion validation, private replay cloud read-after-write, genuine unseen signed blind, model rights and Golden human approval. H06 still has 1,944 known FP and 24,029 known FN; H04/H08 major defects remain. No Phase4, L03, LocalWorker, B L04/L07, Public/C08 or Golden change.

**Ledger:** one known P0 case partially improved in shadow, two unchanged; formally accepted P0=0, P1=0; unresolved H04/H06/H08=3. No model download or RDC use. iPhone user acceptance is post-production deployment, not a pre-deploy blocker.

## 2026-11-02 source-only terminal-branch safety correction (research-only)

A code review found a structural gap in the shadow candidate: checking only the total number of 4-connected owner components does not prevent progressive erosion of a one-pixel-wide terminal branch. The previous `_safe_to_remove` accepted a candidate with exactly one 4-neighbour; repeated passes could remove a thin sleeve/arm-like branch entirely while the component count stayed unchanged. A conservative fail-closed guard now refuses removal at these endpoints. A synthetic negative regression specifically covers this case. This is a structural safety fix, **not** a demonstrated signed-image P0/P1 quality improvement. The H06 11,551→1,944 and 294 genuine coat loss figures above belong to the *previous* candidate version and must not be attributed to the corrected head until signed replay. Exact PR-head canonical QA, signed H04/H06/H08 replay, critical-part visual assessment, private Drive readback and independent blind are still pending. Formal P0/P1 accepted 0/0; unresolved cases 3; L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## 2026-11-02 frozen-input and 8-connectivity contract (source-only candidate)

The function previously verified signed source bytes but accepted class-map and owner arrays without their own pins. This could mix Run30 and a later composed owner under the same source SHA. Both uint8 C-order arrays now require exact SHA-256 pins; mismatches fail closed before the proposal. Per-owner 4- and 8-connected component counts are both checked. This remains a shadow-only, source-only safety change, not an actual signed-image P0/P1 improvement. Updated-head tests, signed H04/H06/H08 replay, critical-part/occlusion quality and canonical QA remain pending. Prior H06 numbers belong to earlier candidate heads. Accepted P0=0/P1=0; H04/H06/H08 unresolved=3; L02 HOLD, Phase4 FAIL, L03/production NO_GO, Golden HOLD. No B, Public/C08, LocalWorker or Golden changes.
