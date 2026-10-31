# Lane A L02: H06 bag/outerwear occlusion disagreement, 2026-11-01

**Research postscore only. Not a quality fix. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Goal and independent evidence

Investigate H06's visually major garment/underlayer and foreground-bag confusion without modifying a signed source, a reviewed label, an inference input, an owner, or a Golden. Compare the **already-frozen** SegFormer-B2 Fashion class-ID prediction, Run30 owner map, and independent DeepFashion2 outerwear prediction to the signed human masks **after** the source-only candidate has been fixed. Source data remains in the existing private Drive evidence folder; this report contains only aggregates.

Verified private input archives (full ZIP SHA-256):

- Signed reviewed evidence: `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`.
- Run30 frozen owner masks: `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`.
- Frozen sleeve-semantic class IDs: `MinimalizerLocal_L02_SleeveSemanticIndependent_PRIVATE_20261016.zip` (private Drive; no class array published).
- Frozen independent outerwear: `MinimalizerLocal_L02_DeepFashion2_OUTERWEAR_SHADOW_PRIVATE_20261016.zip` (private Drive; no prediction array published).

The original signed H06 RGB visually contains a foreground shoulder bag and its strap crossing the coat. The frozen class-ID map identifies a contiguous bag/strap region, but a single model's bag class is **not** ground truth and cannot itself relabel reviewed outerwear or authorize accessory owner promotion. The human outerwear reference also covers part of the visually foreground bag; that conflict is flagged, not silently resolved.

## Reproducible source-free aggregate result

The standalone audit `tools/research/local_l02_bag_occlusion_postscore_research.py` accepts frozen class IDs, frozen owner, alpha domain, independent outerwear support and human reviewed positive/negative masks. It never generates, returns, modifies, saves, or infers any pixel mask. Reviewed labels are consumed **only for postscore**, never candidate construction. The H06 result is:

| H06 bag-class25 partition | Pixels |
| --- | ---: |
| Visible class25 candidate | 22,087 |
| Overlap with reviewed outerwear (contested) | 9,913 |
| Overlap with reviewed non-outerwear | 0 |
| Unknown reviewed region | 12,174 |
| Already assigned to any Run30 owner | 0 |
| Independent DeepFashion2 outerwear overlap | 6,586 |
| DeepFashion2 overlap also reviewed as outerwear | 6,586 |

All partitions balance exactly: 9,913 + 0 + 12,174 = 22,087. H04 and H08 each have **0** class25 candidate pixels under the same frozen source-only predictions. These are known-case observations, **not** an unseen character blind result, not verified bag truth, and not an improvement to the original official quality score.

## Safety and next engineering decision

- Do **not** convert all 9,913 contested pixels to garment or bag owner, or retroactively edit reviewed labels. A bag-aware independent positive observer and an occlusion/visibility review are needed before any semantic owner change.
- Do **not** subtract the contested pixels from official known positives or redefine a quality PASS. The new audit is a **separate disagreement ledger**; official H04/H06/H08 known-case FAIL remains intact.
- Keep H06 underlayer/arm FP, H08 remaining sleeves, H04 regression and Phase4 exclusivity/connection/critical-part retention as P0. Unknown pixels stay unknown.
- The separate SCHP-LIP20 observer lacks a bag class; SCHP-ATR18 has a bag class but remains an **unexecuted candidate** with dataset/licensing and signed-character validation gates. No private images were sent to a remote inference provider.
- Synthetic fail-closed audit tests passed locally (10/10), as did compileall. These do not replace exact PR-head canonical QA, owner-PC tests, true unseen signed blind, model licensing, or human Golden approval. **Accepted P0/P1 fixes 0/0, unresolved major known cases H04/H06/H08 = 3.**

No changes to B L04/L07, Public/C08, LocalWorker production, or Golden.
