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


## 2026-11-02 independently replayed exact-head semantic-collision audit (source-free)

At PR head `91bfc39caa88d289f6451029cbae1b44a692a210`, the exact research module Git blob `5f7d4254d8ff92017f6973b5fb0891295e9453fc` was reconstructed byte-identically and executed on authenticated signed H04/H06/H08 source RGB/alpha, frozen Run30 4-neighbour owner and frozen SegFormer class maps. Source SHA, class-map SHA, owner SHA and four existing private ZIP SHA pins matched; candidate outputs were frozen before the separately loaded human postscore. **This is the current head, not an older PR-body checkpoint.**

- H04: 0 changed; known FP 4,423, known FN 3,186 remain.
- H06: 6,548 owner pixels abstained; known false owner **11,551 → 5,385**, comprising **6,095 known underlayer + 71 known arm** removals. But **208 genuine coat pixels also erased**, and 174 removed pixels are unknown (not negatives). Reviewed garment FN 23,735 → 23,943. Four- and eight-connected owner component counts remained [0,9] and [0,8]. Candidate owner SHA-256 `623d357a9d0a05378d6c07857e6ace5d03b51834bc684d36024ef21915fcb881`.
- H08: 0 changed; known FN 60,035 persists; 4/8 component counts unchanged.

**New independent-observer exclusion finding:** all **208** genuine H06 coat pixels wrongly removed by this candidate have **no positive DeepFashion2 outerwear prediction**. The independently frozen AnimeSeg class map places **all 208** in class 11, but also places **5,532 known false-owner pixels** removed by this candidate in the *same* class 11 (plus 157 unknown removed pixels). Thus neither a blanket DeepFashion2-positive preservation rule nor a blanket AnimeSeg-class-11 veto separates the important genuine coat from underlayer/arm on this signed case. These labels were used strictly in *post-inference diagnosis*, not as candidate inputs or threshold tuning. A new independently licensed semantic/subpart observer is needed before an owner promotion; do not derive a new class11 rule from this exposed case.

**Visual check:** the signed source-pixel-only H06 owner cutout still exhibits major missing body/garment regions despite its numerical FP reduction. No full-character P0 is resolved. The newly created deterministic private replay archive (10 members, SHA-256 `8bb5325784b3d24959d7880258d32f877549f0624110c672190739f2d6305d29`) could **not** be uploaded to the existing private Drive folder because the approved file-upload path returned `container_session_unavailable`. It is **not cloud-preserved** and no read-after-write is claimed. Private source/NPZ/masks remain outside GitHub.

**Promotion:** accepted P0=0, P1=0; H04/H06/H08 unresolved=3. Current candidate still violates genuine-garment preservation. Canonical full QA, source-only Phase4 critical-part/occlusion PASS, unseen signed blind, rights, Golden and production acceptance are pending. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** B L04/L07, Public/C08, LocalWorker production and Golden unchanged.

## 2026-11-02 cross-owner contact preservation correction (source-only, not quality PASS)

The prior local deletion rule and per-owner 4/8-component counts did **not** protect contact between *different* owners. A class32 sleeve boundary pixel adjacent to an arm could be deleted without changing either owner's component count, disconnecting the arm-to-sleeve contact while all existing component-count postconditions passed. A source-free 72×72 reproduction confirmed that the previous local topology rule permits this deletion.

The A-only research candidate now computes a **frozen eight-neighbour cross-owner contact mask** before making any proposal. Every original owner1/owner2 contact pixel is immutable in the shadow candidate, and the postcondition explicitly rejects any such deletion. The source-free receipt records the number of protected contact pixels and confirms preservation. One targeted negative regression is added. This conservative safeguard may reduce the number of H06 false-owner pixels removed; **do not reuse earlier H06 11,551→5,385 or 208 true-coat-erasure metrics for this new head**.

GitHub source/test updates were read back by exact blob SHA. A small source-free geometry reproduction confirmed the unsafe predecessor's local deletion and the new contact mask's protection. **The exact updated-head complete pytest suite, signed H04/H06/H08 replay, independent observer comparison, full canonical QA and private Drive evidence upload/readback are not yet verified.** No real-image P0/P1 improvement is claimed. No human labels are accepted as inference inputs; no owner promotion or production change. Accepted P0=0/P1=0; H04/H06/H08 unresolved=3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## 2026-11-02 exact current-head signed replay and canonical preservation attempt

The **exact remote** A-only module and test blobs were reconstructed and independently verified against Git blob SHA-1: module `1bd0fa8fe2ed825b89959ff3de74bcef1e7acb9a`, tests `2a6afbfd3bfb6a2b8faae406b0df1defac099e78`. The isolated source-free pytest suite on the current `c197bffd98ce7e7deb6483f698db718803779c58` head passed **11/11**, and Python compilation passed. This is **not** the full canonical four-stage QA or CI.

The canonical non-shared Drive's four original private archives were re-materialized and their full SHA-256 checked against existing pins: reviewed `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, sleeve `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, DeepFashion2 `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`. H04/H06/H08 signed original source SHA matched Run30 external receipts; frozen class and owner arrays were independently pinned before proposal. The current-head shadow was replayed twice per case, yielding identical owner bytes and receipts. Human reviewed labels were loaded **only after** all proposals were frozen.

- **H04:** 0 changed; known FP 4,423; known FN 3,186. Candidate owner SHA `5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e`.
- **H06:** 6,548 owner pixels abstained; known FP **11,551→5,385** (6,095 underlayer and 71 arm removed); **208 genuine coat pixels erased**, 174 removed pixels unknown (unscored); known FN 23,735→23,943. Candidate owner SHA `623d357a9d0a05378d6c07857e6ace5d03b51834bc684d36024ef21915fcb881`. Both 4- and 8-connected component counts unchanged; pre-existing 8-neighbour cross-owner contacts preserved.
- **H08:** 0 changed; known FN 60,035 remains; candidate owner SHA `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`.

**Important new exact-head finding:** the cross-owner contact guard added at head `c197bffd` does **not change the H06 owner output** compared with the prior signed replay (`623d357a...`); it protects a real structural invariant but provides **no new actual-image P0 recovery**. H06 still violates the pre-existing frozen-owner no-erasure promotion contract. Do not merge/promote this candidate, count this as unseen generalization, or mistake topology for critical-part visual quality.

A deterministic **private-only** six-member replay archive was produced locally (SHA-256 `a5772a09a7d7171fd199120a7f03744efe25afb570bb0c50eff67ecda8246386`). The exact canonical Drive folder upload failed twice with `container_session_unavailable`; **no cloud save or read-after-write was achieved**. Do not cite the local archive as preserved evidence. The four original authenticated source archives remain in canonical Drive; the source-free hashes and postscore above are recorded here. No private pixels, masks, source coordinates or NPZ are committed.

**Accepted P0=0, P1=0; H04/H06/H08 unresolved=3; no merge.** Next decisive gates: independently supported H06 true-coat retention and H08 sleeve recovery, source-only Phase4 critical-part/contact/exclusive-owner quality, exact-head full QA, genuinely unseen signed blind, model/data rights, and separate human Golden. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO**. No Lane B, Public/C08, LocalWorker production or Golden change.


## 2026-11-02 Run30 source/class/owner provenance binding (source-free, research-only)

An integrity gap was reproduced with the exact prior PR algorithm: pairing **H06 signed original RGB/alpha and Run30 owner** with **H08's frozen class map** (same dimensions), then supplying newly computed SHA-256 values, passed all generic input checks. It abstained because of color separation, but **did not detect the cross-character provenance mix**. A hash computed by the same caller proves byte consistency, not that three arrays came from the same signed Run. This is a P0 evidence-integrity issue, not a demonstrated new visual defect.

Added `propose_pinned_run30_4_shadow` as the required historical replay entrypoint. It independently binds each of the **three known H04/H06/H08 cases** to the exact frozen source bytes, SegFormer class-map bytes, and **Run30 4-neighbour** exclusive owner bytes, using SHA-256 triplets derived from the four previously authenticated private Drive ZIPs. Wrong-case, modified or cross-run triples now fail closed with `RUN30_PROVENANCE_TRIPLE_MISMATCH`; unregistered cases fail with `UNPINNED_RUN30_CASE`. The generic helper remains explicitly exploratory and **must not** be cited as independently authenticated replay. The pins contain only source-free digests, not private pixels, masks or coordinates. No unreviewed 8-neighbour or unknown-character provenance is authorized.

**Exact source verification:** the locally executed Python module was byte-for-byte matched to the GitHub A-branch Git blob. The pinned entrypoint was executed on the actual signed H04/H06/H08 4-neighbour source/class/owner triples. It reproduced H04 **0**, H06 **6,548**, H08 **0** changed owner pixels; H06 lost **208 known correct coat pixels**, removed **6,166 known non-outerwear pixels**, and changed **174 unknown pixels** (unknown not counted negative). The deliberately mixed H06 source+owner/H08 class map is rejected by the pinned wrapper. Three source-free negative tests PASS locally. The existing generic algorithm and image-quality outcome are unchanged.

**No new accepted P0/P1 quality improvement**: accepted P0=0, P1=0, H04/H06/H08 unresolved=3. The historical signed images are exposed known cases, not an unseen blind. This fixes replay provenance integrity only; it does not resolve H06's 208-pixel correct-coat loss, H08 sleeve gaps, H04 errors, or independent semantic ownership. Exact-head full-repository QA/CI, unknown signed blind, independent observer, Phase4 owner exclusion/connection/critical-part quality, model rights and Golden approval remain pending. Keep PR Draft and unmerged; **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO**. B, Public/C08, LocalWorker production and Golden untouched.


## 2026-11-02 local negative-space topology guard (source-free review)

A fresh review of the exact A-only class32 abstention helper identified another P0 structural failure mode: its 4-connected foreground retention test could remove a pixel surrounded by foreground on four sides while diagonally adjacent to background. The foreground owner component count would stay unchanged, yet a **new four-connected enclosed background void** could be created. This is distinct from the previously protected frozen cross-owner contact and endpoint erosion. A 7×7 source-free counterexample reproduced the local condition: the 3×3 negative-space component count changes **1→2** under four-neighbour connectivity.

The A-only research helper now conservatively requires both four- and eight-neighbour local negative-space component counts to remain unchanged before any class32 owner abstention. Added one rejection regression and one permitted-boundary control. The isolated helper reproduction passed 2/2 structural checks. GitHub source and test blob read-after-write succeeded. **The exact updated PR-head pytest suite, signed H04/H06/H08 image replay, global hole-count/critical-part visual QA and canonical merge-readiness verification have NOT run for this head.** This local guard is necessary but not sufficient to certify full-image topology, so Phase4 remains FAIL.

Do not reuse H06 historical 11,551→5,385 known FP or 208 true-garment erasure metrics for the newly guarded head without signed replay. The frozen owner candidate has not been promoted; the known H06 true-garment preservation problem, H08 missing sleeve, H04 errors, unknown signed blind, model/data rights and private Drive evidence remain unresolved. **New accepted P0 fixes 0, P1 fixes 0; unresolved H04/H06/H08 3; no main merge. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No Lane B, Public/C08, LocalWorker production or Golden changes.

## 2026-11-02 independently reconstructed signed-input replay (mirror, not exact-head QA)

The canonical non-shared Drive bundles were materialized read-only: ReviewedEvidence SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 frozen 4-neighbour owner SHA-256 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, and SleeveSemantic SHA-256 `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`. All three case-specific source PNG, class-map and owner-array SHA-256 triples matched the pinned registry in the A-branch helper. The algorithm was **independently reconstructed** using NumPy/OpenCV/SciPy/Pillow, including 4/8-neighbour local negative-space guards and frozen cross-owner contact protection; it was **not** imported byte-for-byte from the exact GitHub PR head, so its numeric output must be confirmed by canonical exact-head replay before release decisions.

After freezing each source-only candidate, existing private human labels were used for evaluation only. Mirror outcome: H04 owner unchanged (known FP 4,423); H08 owner unchanged (known FP 0, missing sleeve unresolved); H06 **7,296** owner pixels abstained, comprising **6,847 reviewed non-outerwear**, **239 reviewed correct garment**, and **210 unreviewed** (unknown, not negative). H06 known FP **11,551→4,704**, known garment TP **291,088→290,849**. The mirror's full-frame four-neighbour enclosed-hole counts were unchanged for each owner on all three cases. The **239 correct garment erasures are a P0 promotion blocker**; the lower known FP count is not an accepted quality fix. Differences from historical H06 6,548-pixel/208-true-erasure metrics require exact-head reconciliation; neither metric may be silently promoted.

No new signed images, model inference, generated pixels, owner promotion, Golden changes, or private artifact publication. This is a diagnosis of the existing H06 owner-erasure problem, not an unseen blind or an actual rendered-quality improvement. **Accepted P0=0, P1=0; unresolved H04/H06/H08=3.** Next: run exact PR-head replay and full Phase4 critical-part/occlusion/owner exclusivity QA, obtain independent licensed garment/underlayer semantics, repair H06 true garment erasure and H08 sleeve loss, then private evidence Drive read-after-write and formal merge-readiness. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## 2026-11-02 independent full-frame true-coat-loss clustering audit (HOLD)

An independent NumPy/OpenCV/SciPy reconstruction (NOT byte-exact current PR-head execution) re-read the canonical signed ReviewedEvidence, Run30 owner and SleeveSemantic Drive ZIPs; all three archive SHA-256 pins and all H04/H06/H08 source/class/owner SHA triples matched the A-only registry. Human labels were loaded only after the source-only owner candidates had been frozen. The H06 mirror again abstained **7,296** pixels, including **6,847 known incorrect owner**, **239 reviewed true-coat loss** and **210 unknown**. These values are not newly credited improvements and are not interchangeable with the earlier exact-head 6,548/208 receipt.

**New P0 risk localization:** the 239 erased genuine-coat pixels are distributed across **10 four-connected loss components**, the largest containing **141 pixels**. This is not proof that the losses are harmless boundary noise. H06's full-frame owner2 enclosed-hole counts remain **25→25 (4-neighbour)** and **17→17 (8-neighbour)**; unchanged global topology does **not** imply garment retention. H04 and H08 owner candidates remained unchanged in the mirror. H06's frozen 8-neighbour cross-owner contact mask is empty, so that guard cannot resolve its underlayer-vs-coat semantic confusion.

A new private-only candidate-owner/overlay/postscore ZIP was constructed and internally SHA-checked (`e7d86272ca6268a78c43e121afd935d707c6055fcd22fe344c6035f0499a765d`), but uploading it to the existing non-shared Drive folder failed with `container_session_unavailable`. **Do not count it as remotely preserved or source it from GitHub.** Existing canonical private source archives remain unchanged. This is a diagnostic quality **FAIL**, not an admitted P0 fix, a full exact-head QA, or an unknown-character blind. Accepted P0/P1=0/0; unresolved H04/H06/H08=3; Draft unmerged; L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO. Next priority remains independently licensed coat/underlayer/arm semantics and a no-true-coat-erasure Phase4 replay, not another known-case threshold tweak.


## 2026-11-03 opt-in garment-seed-scale retention candidate (known H06, HOLD)

A new **opt-in**, source-only conservative retention guard was added to the A-only research helper. The existing default candidate is unchanged. With the opt-in enabled, the frozen class5/10 garment-owner pixels determine a geometric scale: the median interior Euclidean distance to their boundary. An existing class32 owner pixel within that distance of the garment seed is **protected from deletion**. This uses signed RGB/alpha, frozen class IDs and frozen owner only. It does not use human masks, annotations, coordinates, newly generated pixels or independent-model claims. The geometric rule was devised after examining known H06; **it is an exposed known-case hypothesis, not unseen-character generalization**.

Authenticated source-only inputs were read from the canonical private Drive bundles: ReviewedEvidence ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, Run30 4-neighbour owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`. H06 signed source, class and owner byte SHA-256 all matched the pinned registry. An **independently reconstructed** source-only replay, not the exact updated GitHub module, produced the following postscore after the proposal was frozen:

| Known H06 Run30 source-only shadow | Existing reconstructed candidate | New guarded reconstruction |
| --- | ---: | ---: |
| Total class32 owner pixels abstained | 7,296 | **6,872** |
| Reviewed incorrect owner removed | 6,847 | **6,701** |
| Reviewed correct garment accidentally removed | **239** | **10** |
| Unreviewed pixels removed (unknown, not negatives) | 210 | 161 |
| Known incorrect owner remaining | 4,704 | 4,850 |
| Owner2 4/8 components | 9/8 | 9/8 |
| Owner2 4/8 enclosed holes | 25/17 | 25/17 |

The source-only garment-seed interior median was **28.861739 px**, protecting **18,973** pre-existing class32 owner pixels. The new reconstruction retained **229 more reviewed correct garment pixels**, at the cost of retaining **146 more known incorrect owner pixels**. This is a material *known-case trade-off*, not an accepted P0 fix. **Ten correct garment pixels are still erased**, 4,850 known incorrect H06 owner pixels remain, and the actual visual garment/arm/cuff semantics are unresolved. H04's frozen garment/competitor color separation is below the existing guard's fixed minimum (no abstention), while H08 has no occupied class32 owner target for this removal helper. Neither H04 nor H08 major defect is resolved.

The A-only GitHub helper now supports `protect_garment_seed_scale=True` as a strictly boolean opt-in, preserving default behavior and the pinned source/class/owner replay contract. A postcondition and source-free receipt record the protected-owner invariant. Three source-free negative/contract regression tests were added. **The updated GitHub code and tests have been written and read back, but their exact-head execution, full canonical QA and exact signed replay have NOT yet passed.** The independent reconstruction above must not be mislabeled exact-head QA or merged into Phase4.

**Accepted real-image P0=0, P1=0; H04/H06/H08 unresolved=3.** PR remains Draft, unmerged. Source-only Phase4 critical-part/occlusion and no-erasure promotion gate FAIL; independent garment/skin/underlayer observer, genuine unseen signed blind, model rights, exact-head QA, private replay Drive cloud read-after-write and human Golden are pending. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No B L04/L07, Public/C08, LocalWorker production or Golden changes.

### 2026-11-07 exact-head signed replay

The current A branch HEAD `3299dea03d20d30cf0741a113eac269577bd51f8` was replayed locally with the pinned H06 Run30 4-neighbour source/class/owner triple. The signed source SHA, frozen class SHA and frozen owner SHA all matched the registry. The replay remained source-only and did not accept review masks as inputs.

| Exact-head H06 shadow | Result |
| --- | ---: |
| class32 owner pixels abstained | 5 |
| reviewed underlayer owner removed | 1 |
| reviewed arm owner removed | 3 |
| reviewed correct outerwear removed | 0 |
| reviewed unknown owner removed | 1 |
| owner 4/8 components | unchanged: 9/8 |
| owner enclosed holes 4/8 | unchanged: 25/17 |
| Phase4 / L02 / production | FAIL / HOLD / NO_GO |

This is an exact-head integrity and no-erasure replay, not a semantic quality PASS. The remaining H06 wrong-owner pixels require a separately authenticated observer that distinguishes explicit non-garment from unknown; the existing observer agreement artifact is positive shadow evidence only and cannot authorize deletion by absence. No owner promotion, merge, or production change follows from this replay.

The source-free H06/H08 candidate owner maps and replay receipts were preserved privately with the H08 exact-replay record; no source image, review mask or coordinate data was added to GitHub.
