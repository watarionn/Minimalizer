# Lane A L02: signed H06 cuff underlayer, independent-observer mismatch (2026-10-25)

**Known signed character, source-only research, negative result. No owner-3 promotion. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Provenance and source-only freeze

The four canonical non-shared Drive research archives were materialized from the adopted `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence` hierarchy. Their ZIP SHA-256 matched the previously pinned values: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemanticIndependent `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. The internal reviewed/Run30/AnimeSeg manifests verified 19/7/5 members. The embedded original H06 WebP bytes were independently checked against the signed review audit before decoding.

Using only the signed original RGBA, frozen SegFormer class IDs, frozen Run30 owner and frozen AnimeSeg observation, the existing hue-abstention + neutral source-only component rule reproduced the prior provisional **10,484px / 2 components** candidate. Its mask SHA-256 is the previously recorded `df86e0ad3b018e1c25a996c2d9d1788f58865b41a496780a5408a2acbaff770e`. Source-only probes were frozen before human masks were opened. No annotation coordinates or human masks entered inference.

## Substantial independent-observer disagreement

On that original-source neutral cuff candidate, frozen AnimeSeg class IDs distribute as **class11: 9,389px; class10: 977px; class0: 118px**. Therefore treating class11 as a hard negative for underlayer would discard **89.6% of the candidate**. The postscore-only human review shows the 9,389 class11 pixels include **9,102 correctly reviewed underlayer**, **49 reviewed arm**, **8 reviewed outerwear**, and **230 unreviewed**. The generic-clothes class10-only rule retains just **977 correctly reviewed underlayer** and drops most of the visible cuffs. **Do not turn AnimeSeg class11 into an underlayer-exclusion rule or treat generic-clothes class10 as complete underlayer coverage.** This is a concrete observer/domain mismatch, not proof that the human review or model is globally correct.

For completeness, two source-only, previously adopted fixed-shape/color policies were frozen and evaluated, not optimized from review labels:

| Frozen candidate | Total source pixels | Reviewed underlayer | Known arm intrusion | Known coat intrusion | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Existing neutral cuff candidate | 10,484 | 10,177 | 49 | 8 | 250 |
| AnimeSeg class10 only | 977 | 977 | 0 | 0 | 0 |
| Existing LAB 25 distance from each component's source median | 8,866 | 8,623 | 35 | 7 | 201 |
| Existing 3x3 full-mask opening + component floor | 10,475 | 10,172 | 48 | 6 | 249 |

The class10-only and LAB policies destroy large correct cuff areas; the 3x3 opening removes only 1 of 49 known arm intrusions. **All three are rejected**, not owner-3 or production candidates. The existing provisional candidate also remains unapproved because its 49 arm + 8 coat intrusions are real semantic defects and 250 pixels remain unknown. No thresholds were retuned after postscore.

## Engineering consequence and gates

The visually meaningful H06 missing white cuffs are not safely recoverable merely by AnimeSeg class10/11 filtering, LAB-median clipping, or 3x3 morphology. An independent **cuff-versus-skin** semantic source observer, or a rigorously supported abstention scheme that preserves the cuff while excluding arm/coat, is needed. The model's class labels are observations, never automatic semantic owner authority. H06 composed-owner provenance and its separate 10,484px provisional layer remain unchanged; this study does not modify the composed coat, Golden, production, or user review.

**New accepted P0/P1 resolutions 0/0; H04/H06/H08 major cases unresolved 3.** Full repository CI, genuinely unseen signed blind, Phase4 exclusive-owner/critical-part quality, Phase5, Golden and iPhone acceptance remain pending/FAIL. This note contains source-free counts only. No original images, masks, NPZ, private review geometry, or coordinates are committed. Lane B L04/L07, Public/C08 and production LocalWorker remain untouched.
