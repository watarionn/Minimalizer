# Lane A L02: class30 cannot inherit class32 observer support (2026-10-25)

**Research-only source-free safety correction. Not a signed latest-frontier quality improvement. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Root cause and code

The existing mixed `eligible_classes=(30, 32)` branch in `local_l02_contact_density_partition_shadow.py` computes independent AnimeSeg generic-clothes support **per combined 8-connected island**. An unsupported class30 subcomponent can therefore borrow class32 evidence and become eligible without any independent evidence on class30 itself. Component topology and source alpha checks do not establish garment semantics.

The A-only change withholds each class30 8-connected subcomponent unless it contains at least 32 **own** AnimeSeg class10 pixels, reusing the already adopted `MIN_INDEPENDENT_GENERIC_CLOTHES=32` constant. No new threshold was tuned from labels; the existing default class32-only path remains byte-for-byte unchanged. A withheld class30 component is not promoted or inferred as a negative. This is an abstention gate, not a model-quality PASS.

## Signed-source independent audit (known cases, postscore only)

The four canonical non-shared Drive archives under `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/` were retrieved and ZIP SHA-256 checked: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemanticIndependent `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Internal member SHA-256 checks passed 19/19, 7/7 and 5/5 respectively.

Using **Run30 frozen owner** and source-only original RGBA/SegFormer/AnimeSeg inputs, before opening human masks, the component-support filter abstained from H08 **74 class30 pixels in one component**, and H06 **54 pixels in two components**. After freezing the abstentions, independent human postscore classified H08's 74 as **74 known arm / 0 reviewed outerwear**, and H06's 54 as **26 reviewed outerwear / 0 known arm / 28 not covered by those two reviewed categories**. These are **eligibility-stage** numbers, **not** changes to an actual composed owner or proof of P0 repair. H04 has no matching AnimeSeg source in this replay and was not re-evaluated. Unknown pixels were not counted as negatives.

The previously signed **latest H08 composed owner** `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086` was not reproduced in this experiment. The existing class30 opt-in at that frontier had previously added 849 reviewed garment pixels and no known FP; this guard must be replayed against that exact latest owner to exclude a garment regression. The known-case H08 source-color/brightness-wide sleeve recovery alternative was also **rejected**: from Run30 it added 44,449 reviewed garment pixels but also 776 reviewed arm pixels, and is inferior to the existing later frontier. No new owner promotion.

## Verification and release decision

Source-only isolated helper fixture confirmed 400 unsupported class30 pixels withheld without touching class32, while 40 independent class30 support pixels retain the component. New source-free regression tests cover these cases and default class32 preservation. Full repository pytest/CI, exact GitHub-head complete replay, unseen signed blind and Phase4 semantic owner quality are **not** established.

**Accepted P0 fully resolved 0 / P1 0; H04, H06, H08 all unresolved.** The new code remains a research-only branch and Draft PR until signed latest-frontier replay, H04/H06 regressions, full CI, and meaningful sleeve/arm visual quality can be verified. No changes to B L04/L07, Public/C08, production LocalWorker, Golden, or release. No private image, mask, NPZ, human polygon or coordinate is committed.


## 2026-10-25 signed latest-H08 replay and critical regression correction

The previous first version of this PR measured class30 support only inside `eligible=(baseline_owner==0)`. This accidentally discarded class30 model evidence on pixels already incorporated into the frozen owner. **Exact signed H08 source-only replay exposed a real 845-pixel reviewed-garment regression**, not a hypothetical risk:

| Latest signed H08 owner | SHA-256 prefix | Reviewed garment TP | Known FP | Garment FN | Known arm FP |
| --- | --- | ---: | ---: | ---: | ---: |
| Current frontier, no class30 guard | `94122b855f70` | 144,221 | 17 | 12,349 | 17 |
| First PR #440 guard (incorrect owner-masked evidence) | `ca76309ed90f` | 143,376 | 17 | 13,194 | 17 |
| Corrected source-domain class30 evidence | `94122b855f70` | 144,221 | 17 | 12,349 | 17 |

**Root cause fixed:** source-only independent class30 support is now counted on each complete 8-connected class30 component inside the original signed source alpha, before any owner-stage eligibility masking. The minimum remains the already adopted 32 AnimeSeg class10 pixels. Class32 support never counts toward class30. Transparent pixels cannot contribute support. No human masks or coordinates enter inference. This preserves class30 sleeve evidence that a previous owner stage had already consumed, without blindly OR-ing mixed class30/32 islands.

The source-only chain was reconstructed from the four SHA-pinned private archives and verified stage-by-stage: H08 composed `3e467694...` → strict `32bb5266...` → single-anchor `6472cfc4...` → class32 palette `f847f995...` → latest mixed opt-in `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`. Source and owner hashes were frozen before postscore. The corrected guard reproduces the same final owner hash and **prevents the 845 true-garment loss**; it does **not** eliminate the existing 17 known arm misassignments or large sleeve gaps.

The separate Run30 eligibility negative remains: H08 74 known-arm / 0 reviewed-garment pixels withheld; H06 54 withheld, including 26 reviewed garment / 0 known arm / 28 other-or-unknown. These are eligibility measurements only. H06's existing composed owner `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c` was independently reproduced unchanged by the default source-only path. H04 is outside the mixed class30 opt-in and has not been re-evaluated with a new observer in this replay.

Two new source-free regressions cover previously-owned class30 evidence and transparent false evidence. **12 focused local tests PASS** (six class30 and six related contact-palette tests), but the locally assembled research dependencies are not certified GitHub-head-exact and full repository CI has not run. Keep PR **Draft/unmerged** until independent exact-head tests, H04/H06/H08 regression review, signed unknown blind and Phase4 quality gates. No P0/P1 case has been formally resolved. No private bytes were committed.
