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

## 2026-11-01 independent-positive negative partition and fail-closed QA

The bag/outerwear disagreement audit now separately counts **independent outerwear positives on explicitly reviewed non-outerwear** inside the tentative class25 bag region. The previous independent-overlap receipt listed positive/unknown counts but omitted the known-negative partition, so a future model conflict could be underreported. All three independent partitions must sum to the independent overlap, and review/owner/independent partitions now raise explicit `BagOcclusionAuditHold` exceptions rather than relying on Python `assert` (which disappears with `python -O`). This is a **postscore receipt integrity correction**, not an inference or owner change.

The exact A-only code/test blobs were independently reconstructed and locally tested: module `86fd08344ab906da893c57a10e761447fe4faadc`, test `27f037d4b63b3ed2c66774993537ac1a4f04a9b5`; isolated 11/11 tests PASS in normal Python and 11/11 under `PYTHONOPTIMIZE=1` (pytest emitted the expected warning about test-module asserts). Python compileall PASS. Signed H04/H06/H08 postscore replay from the four existing canonical private archives, with externally pinned ZIP SHA-256, preserved previous bag totals exactly: H04/H08 class25 0; H06 class25 22,087, reviewed outerwear conflict 9,913, unknown 12,174, independent overlap 6,586. **Independent overlap with explicitly reviewed non-outerwear: 0 in all three exposed cases.** This zero is a known-case result, not evidence of unseen generalization or a semantic bag-ground-truth label. Private arrays and human coordinates remain outside GitHub.

This change does **not** repair any H04/H06/H08 P0 or P1 defect. Accepted P0/P1 fixes **0/0**; unresolved known major cases **3**. Exact PR-head full repository QA, Phase4 owner/connection/critical-part quality, independently executed SCHP model, unseen signed blind, model licensing, Golden and release acceptance remain pending. PR stays Draft; no production or Lane B change. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

### Historical integration overlay (source-free only)

The 2026-10-23 22:53 authenticated source-free staging archive (SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`) was extracted into a temporary isolated QA directory. Overlaying the exact new PR #448 module/test blobs yielded **246 passed, 31 subtests passed** across 34 test files with `PYTHONPATH=.:tools/research python -m pytest -q tests`. This is a useful cross-module regression result, **but the staging archive is historical and not the current GitHub main or an exact full PR-head checkout**. It cannot satisfy the remaining canonical current-main QA or Phase4 quality gate. No source images or masks were included in the overlay or committed.

## 2026-11-01 frozen-taxonomy validation hardening (A-only, no quality promotion)

The postscore auditor previously accepted SegFormer class IDs outside its pinned 47-class vocabulary (0..46), Run30 owner IDs outside the exclusive `0=abstain / 1=jacket / 2=coat` domain, and a caller-selected garment owner ID outside `1/2`. Such mismatches could produce plausible aggregate receipts from a wrong or corrupted prediction taxonomy. The auditor now fails closed with `UNKNOWN_SEGFORMER_CLASS_ID`, `UNKNOWN_FROZEN_OWNER_ID`, or `INVALID_GARMENT_OWNER_ID` before computing any metric. No inference algorithm, owner map, reviewed label, or source pixel changes.

Verified locally with source-free synthetic tests: **14/14 PASS** in ordinary Python and **14/14 PASS** under `PYTHONOPTIMIZE=1` (pytest's expected assertion warning is not a source-code safety bypass). Using the four canonical non-shared Drive archives with full ZIP SHA-256 pins listed above, signed H04/H06/H08 real-array postscore preserved prior bag counts: H04/H08 **0**; H06 **22,087** class25 visible, **9,913** reviewed garment conflict, **12,174** unknown, **6,586** independent outerwear overlap. The three new invalid-taxonomy probes were also rejected for each real case (**9/9**). This validates a safety contract, **not** a repaired P0/P1 image defect.

**Accepted P0 fixes 0, P1 fixes 0; H04/H06/H08 remain unresolved (3).** The exact GitHub PR-head full repository four-stage QA and owner-PC merge readiness are still pending. Keep PR Draft; do not merge, promote L02/L03, or change Golden/production. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
