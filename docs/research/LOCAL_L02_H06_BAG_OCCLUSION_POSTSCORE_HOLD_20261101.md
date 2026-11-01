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

## 2026-11-01 independent H06 P0 root-cause partition (postscore only)

Replayed **unchanged** signed H06 original alpha, frozen Run30 4-neighbour owner, SegFormer class IDs, independent DeepFashion2 outerwear, and the reviewed H06 masks from the existing private Drive archives. Full ZIP SHA-256 pins: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; DeepFashion2 `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`. ReviewedEvidence 19/19 and Run30 7/7 ZIP member SHA checks PASS. Original H06 embedded WebP decoded alpha and frozen reviewed alpha have equal visible-pixel count **602,869** and were checked for domain alignment. This is a **historical Run30** diagnostic, not the newer strict/composed frontier; do not mix its absolute counts with those of a later owner.

**Two distinct causes of missing reviewed garment, not one class32 threshold problem:** Run30 H06 has **23,735** reviewed outerwear FN. Exactly **9,913** (41.77%) coincide with visible SegFormer class25 bag candidate; **13,822** (58.23%) do not. The non-bag FN are class0 **6,042**, class7 **4,203**, class30 **3,577**. This is a postscore taxonomy of known FN, **not** a bag-ground-truth claim and not a permission to add those pixels. The original known-positive mask is unchanged.

**Why blanket class32/component/DeepFashion2-negative veto is unsafe:** Run30 H06 has **46,613** assigned class32 pixels: reviewed outerwear **31,074**, known underlayer **11,326**, known arm **225**, unknown **3,988**. Only **311** of the 31,074 true outerwear pixels have independent DeepFashion2 positive support, leaving **30,763 true outerwear pixels** without that support. Thus, treating missing DeepFashion2 support as a negative would erase substantial correct garment. In 4-connectivity, class32 assigned owner has **6 components**; in 8-connectivity **5**. In both, the same **two mixed components** contain **30,763 known true outerwear pixels plus all 11,551 known underlayer/arm false-owner pixels**, together **46,247 owner pixels** including unknown. There are **zero pure-known-false components** eligible for a safe whole-component veto. Whole-component removal would destroy 30,763 correct garment pixels. This is a structural counterexample to component-only abstention and blanket independent-negative gating, not a proposed owner change.

Reproduction method: on the frozen arrays, form `assigned32 = (owner != 0) & (classids == 32)`; use `scipy.ndimage.label(assigned32, generate_binary_structure(2, 1 or 2))`; intersect components with reviewed outerwear, underlayer and arm masks **only after freezing the owner**. Count class25 intersections separately with reviewed outerwear FN; keep all unlabeled source pixels **unknown**. No labels, component IDs, coordinates, private arrays, original images or masks are committed to GitHub.

**Engineering consequence:** H06 requires *independent positive evidence* separating sleeve/coat from underlayer/arm **within the same connected component**, plus a separate bag/occlusion decision. Neither a component-wide veto nor class32-only threshold tuning can fix both. H08 sleeve retention and H04 regression remain mandatory. No owner promotion, no Golden mutation, no release. **New accepted P0=0, P1=0; unresolved H04/H06/H08=3; Phase4 FAIL.**

## 2026-11-01 signed-alpha domain guard and exact-source replay

The existing postscore auditor accepted an `independent_outerwear` mask with positives outside the signed source alpha because those pixels were silently excluded by the visible bag intersection. That is a **provenance validation gap**, even when the final aggregate happens to be unchanged. The A-only research code now raises `INDEPENDENT_OBSERVER_OUTSIDE_SOURCE_ALPHA` before producing any receipt. This does not turn model absence into negative evidence or change owner assignment.

The exact new GitHub module and test blobs were reconstructed independently and checked by Git blob SHA-1: module `6d84ecafe015a9a8be39079c2afd6a63f7e780f9`, test `f6c91fe5afa7092e1374459265cacb00be38d83b`. The isolated test file ran **11/11 PASS**; a separate new invalid-alpha negative and unchanged signed H04/H06/H08 aggregate replay ran **2/2 PASS** in the local research sandbox. The four private source archives were read from the established non-shared Drive folder and verified by full ZIP SHA-256: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, DeepFashion2 `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`.

Unchanged Run30 4-neighbour postscore: H04/H08 visible class25 bag **0/0**, H06 **22,087** with **9,913** contested reviewed outerwear, **12,174** unknown, **6,586** independent DeepFashion2 overlap. All independent positive masks were within source alpha. No human label was supplied to inference, no owner or source pixel changed. This is a **safety-contract correction only**, not P0/P1 quality improvement. Canonical four-stage QA and exact PR-head full-repository validation remain pending; PR stays Draft and must not be merged on the isolated test result alone. **Accepted P0/P1=0/0, H04/H06/H08 unresolved=3, L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
