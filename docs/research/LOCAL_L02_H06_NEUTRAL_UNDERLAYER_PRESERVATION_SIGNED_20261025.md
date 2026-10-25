# Lane A L02: preserve H06 source-neutral underlayer as a separate shadow (2026-10-25)

**Status: research-only Draft candidate. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No change to production inference, LocalWorker, Lane B, Public/C08, Golden or human approval. The H04/H06/H08 corpus is exposed; this is **not** unseen generalization.

## P0 mechanism and visible comparison

The integrated H06 class32 hue-abstention removes most wrong coat ownership but leaves removed original-source pixels unowned. The source-only `neutral-underlayer-preservation-shadow` preserves coherent, achromatic removed class32 pixels as a **separate, unapproved provisional layer**, while keeping the coat owner and 4/8 connectivity from the existing hue stage. It uses the existing fixed neutral hue condition (`saturation < 0.15`, `value > 0.50`) and existing 8-connected component floor (1,024px), not a new per-character postscore threshold. The source-only proposal has no human annotations, coordinates, polygon geometry, generation, inpainting or alpha expansion. It deliberately refuses mixed jacket/coat-owner cases such as H08.

Four canonical non-shared Drive ZIP archives were independently verified against the existing SHA-256 pins. Internal reviewed/Run30/AnimeSeg manifests verified 19/7/5 members. The embedded signed H06 source SHA matches `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`. Two source-only frozen replays and their postscore receipts are byte-identical (source-free report SHA-256 `d1750251344cbcab0c616545687e5c7ad207334037ec92ae2321b10285c94c3b`). No private RGB, NPZ, masks, coordinates or comparison image are committed.

| Signed H06 known review | Run30 frozen coat | Existing hue-abstained coat | Separate provisional layer |
| --- | ---: | ---: | ---: |
| Correct coat TP | 291,088 | 291,080 | not a coat owner |
| Missing coat FN | 23,735 | 23,743 | not a coat owner |
| Known coat false-owner FP | 11,551 | 1,077 | not a coat owner |
| Wrong underlayer in coat | 11,326 | 1,077 | not a coat owner |
| Correct reviewed underlayer retained separately | not represented | not represented | **10,177px** |
| Wrong arm / coat in provisional layer | n/a | n/a | **49 arm + 8 coat** |
| Unreviewed provisional pixels | n/a | n/a | **250 unknown** |

The source-only provisional layer has **10,484 source pixels across two components**. Private visual comparison shows original sleeve-cuff material retained separately from the tan coat rather than assigned to the coat. However, the 49 arm and 8 coat pixels are real semantic errors, and the 250 unreviewed pixels remain unknown. The provisional layer is **not an accepted semantic owner** and must not be rendered as underlayer without further independent evidence.

**Important frontier distinction:** this replay starts from the authenticated Run30 owner and the existing hue-abstention code. It does **not** reconstruct the later composed H06 frontier of **294,020 coat TP / 1,077 known FP / 20,803 FN**. Do not present the Run30-to-hue improvement or this separate provisional layer as a new accepted H06 coat-quality improvement. New accepted P0/P1 improvements: **0 / 0**; one substantial **provisional** H06 underlayer-retention candidate, zero resolved P0 cases, all H04/H06/H08 unresolved.

## Integration gates

This proposal may be staged only as dormant A research code. Before promotion: independently replay against the latest composed H06 owner, eliminate or explicitly reject arm/coat intrusion without sacrificing large correct underlayer regions, prove source-only Phase4 exclusive owner/connection/critical-part retention, run full CI and genuinely unseen signed blind, then Phase5 exact replay and user Golden/iPhone acceptance. Do not tune from the known H06 review labels. The generic-clothes observer is not specialized underlayer authority. No new model license or production permission is inferred.


## 2026-10-25: signed H06 composed-frontier provenance replay

**The previously missing frontier comparison is now reproduced, but this is NOT a new semantic quality improvement.** Four existing non-shared Drive archives were reauthenticated against the SHA-256 pins in `LOCAL_L02_SIGNED_EVIDENCE_LOCATOR_AND_CONFLICT_NEGATIVE_20261025.md`; the reviewed/Run30/AnimeSeg member checks are 19/7/5. Source-only composed replay of the H06 signed original and frozen observers reproduced the pre-existing frontier owner SHA-256 `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`. Known H06 coat TP **294,020**, known FP **1,077**, FN **20,803**, arm FP **0**, IoU **0.930738**.

Re-running hue on that *already composed* coat changes **0 pixels** and yields **0 provisional pixels**, because the class32 source pixels were already abstained. This is a provenance loss in the prior PR #436 API, **not** evidence that the underlayer was correctly recovered or absent. The research-only `composed_owner` opt-in now compares the original frozen Run30 owner with the authenticated composed owner, without changing the latter. It retains **10,484 original source pixels** in **2 separate unapproved provisional components**, identical mask SHA-256 `df86e0ad3b018e1c25a996c2d9d1788f58865b41a496780a5408a2acbaff770e` to the earlier H06 candidate. Postscore-only breakdown: **10,177 reviewed underlayer**, **49 arm**, **8 outerwear**, **250 unknown**. The composed coat remains byte-identical, with **3,162 already-existing source-only promotions** (not performed by this preservation function). H08's mixed jacket/coat input remains fail-closed. Two signed-source replays gave identical source-free JSON SHA-256 `ef421df5cf0e248bb45caf014407baef3a7f68c7e8ab62a2ecfdfa06d7d10d4b`.

This **closes only the H06 composed-frontier comparison gap**, not Phase4 or the semantic separation gap. No new accepted P0/P1 improvement (0/0); 3 known P0 cases remain unresolved. In particular, the 49 arm and 8 coat misassignments mean the provisional layer must NOT be rendered, converted into an owner, or promoted. The input `composed_owner` must be independently signed/replayed by the caller: this API validates source/alpha, class domain, no reassignment, permissible promotions and 4/8 component identity but does not itself authenticate the caller's model/archive SHA. Source-free A research only; B, Public/C08, production Worker, Golden unchanged. Full repo CI, unseen signed blind and Phase4 remain pending/FAIL.


## 2026-10-25: P0 composed-owner coat-erasure contract repair

A signed H06 **source-only negative replay** exposed a destructive gap in the prior `composed_owner` input contract: it accepted removal of a 3×3 patch (**9 genuine original class10 coat pixels**) from the frozen owner while the coat component counts remained unchanged (**4-neighbour 9→9; 8-neighbour 8→8**). No human annotations were used to construct this negative. The previous component-identity check therefore did **not** guarantee coat-core retention. A larger deletion of the same kind could erase visibly important clothing while passing topology checks.

The A-only research guard now rejects **any** `composed_owner` removal of a frozen class10 core pixel or class29/30/31 preserved extension. Only class32 abstention is permitted; no new pixels are generated and the original frozen owner remains immutable. Added source-free negative regressions cover both core erasure and extension erasure. This is a **P0 safety regression fix**, not a verified improvement in the actual H06 rendered output: accepted new P0/P1 quality improvements **0/0**, three known cases still unresolved. The existing composed H06 candidate, underlayer intrusion **49 arm + 8 coat** and unknown **250** remain HOLD. No blind generalization, Phase4 PASS, full CI, Golden or production approval is claimed.


## 2026-10-25: class32 composed-owner erasure provenance guard

A **new signed H06 source-only negative** exposed a second coat-retention hole in the Draft input contract. The original frozen Run30 H06 owner, signed original WebP (SHA-256 `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`) and frozen class IDs were independently read from the canonical four private archives. ZIP SHA-256 matched all four pins; reviewed/Run30/AnimeSeg internal member manifests matched 19/19, 7/7 and 5/5. No human labels were used to select the negative.

A contiguous 3x3 patch of **9 already-owned class32 source pixels** in the coat-color hue domain can be erased while preserving both 4-connected coat components **9→9** and 8-connected components **8→8**. Its source saturation is above 0.30 and hue distance from the dominant frozen coat seed is below 45 degrees, so the pixels do **not** satisfy the pinned saturated or achromatic hue-conflict predicate. The previous composed-owner contract accepted this deletion solely because the class was 32 and topology counts were unchanged. The specific private pixel positions are not published.

The A-only Draft code now **recomputes the pinned hue-extended source-only abstention from the frozen RGBA/class/owner** for every supplied `composed_owner` and rejects any additional frozen-owner erasure, including class32 holes not in that independent replay. If hue replay cannot be verified, the composed path fails closed. The existing class10/29/30/31 no-erasure guard remains. Two new source-free negative regressions cover arbitrary class32 erasure and missing hue evidence; the composed positive regression supplies a frozen hue-reference fixture. The 9px test is a small demonstrator of a structural **potentially large P0 coat/sleeve erasure**, not a newly recovered visible area.

**Verification boundary:** the signed source-only counterexample and archive/member checks were independently executed. The updated GitHub tests and the exact composed H06 frontier have **not yet been rerun end-to-end after this guard**; do not claim local/full CI PASS or a newly accepted owner. PR remains Draft. Accepted real-image P0/P1 improvement **0/0**; H04/H06/H08 remain unresolved (3). Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD / production NO_GO. No B, Public/C08, LocalWorker or Golden changes.
