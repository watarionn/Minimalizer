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
