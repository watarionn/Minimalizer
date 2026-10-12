# MinimalizerPublic P0 Stage62-66 source-attested color boundary research (HOLD)

Date: 2026-10-12. Branch: `research/public-structural-recovery-p0-part-preservation-20261011` of `watarionn/Minimalizer`, Draft PR #390. The full-character default Public converter, deployed Stage51 research preview, Local Minimalizer and `main` conversion are not edited.

## Stage62. Immutable input authority / historical candidate scope

Require independently SHA256-pinned original 340x340 RGBA, historical left/right source-owner masks, historical face, unapproved observed background, and frozen Facet40 baseline. Reject owner collisions, SHA tamper, invalid input dimensions, nonbinary masks. Exclude protected face/background/alpha. The historical names `left_arm`/`right_arm` **are not confirmed anatomy** and include source-observed clothing, hair, skin and other parts. Zero independently anatomically verified pixels in either case. There is **no authorization to recolor output**.

## Stage63. Source-medoid candidate diagnostic

Only on the original-eligible pixels, split observed RGB into at most eight deterministic median-cut bins. Represent each bin by an RGB triplet actually observed in that bin (sampled medoid), not a generated or extrapolated color. Never invent pixels, mask extents or semantics. Preserve original shape coverage; this is **a private experimental color study**, not a production image or an approved segmentation. Compare the source RGB L1 diagnostic against a one-source-medoid local baseline as well as the *frozen Public Facet40 image*; two comparisons are mathematically distinct.

## Stage64. Source-edge retention

Audit 4-neighbor same-owner RGB contrast >=90 across eligible original pixels. A candidate palette boundary is recorded if its RGB contrast >=48. The retention metric is only about color contrast within historical source-owner hypotheses; false colors, incorrect anatomy and overall silhouette can still remain. Zero verified skin/sleeve/hair labels. Do not treat high edge recall or low L1 as product quality acceptance.

## Stage65. Experimental real-source observations

| Original | Eligible historical-mask pixels | 8-medoid original RGB L1 | frozen Facet40 original RGB L1 within same pixels | Contrast edges retained / observed |
|---|---:|---:|---:|---:|
| GC001 | 9,160 | 454,502 | 1,305,256 | 2,850 / 3,468 |
| Raden | 20,177 | 401,768 | 1,216,761 | 2,128 / 2,640 |

The source L1 comparison measures a limited source-footprint RGB fit and *cannot* by itself establish more effective minimalism, visual Golden compliance, or fidelity of unlabeled neighboring regions. Private three-panel comparisons show some previously lost hair, clothing and arm color detail, but the complete characters remain coarse and inaccurate in the frozen Facet40 shapes. **NOT FOR PRODUCT PROMOTION.** The reviewer must independently assess which original pixels are skin, sleeve, hair and clothing before allowing their use as such.

## Stage66. Verification and preservation

The four source-only computation/gating stages include 25 Node regression tests, original GC001 and Raden replays, immutable source SHA checks, and private preview atlases. Verify cumulative PR research CI separately, with exact Actions run and job log counts; do not use an extrapolated test number as success proof. Commit source modules/test/docs to research branch only, not `main`. Keep all original photos/RGBA/private diagnostic RGBA/PNGs in canonical Drive below `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage62_66_20261012`.

### Still blocking release

- Independent signed visual/anatomical Golden at complete 340/680 full character, specifically hair, skin, sleeve, tie, arms and background.
- Historical Stage8 whole-scene vertex caps GC001 3,604 > 1,887 and Raden 2,370 > 1,412.
- Original absent content prohibition, original RGB verified only, no eyes/nose/mouth and no generative fill.
- Real iPhone Safari, secure HTTPS origin and rollback tests for future regular converter release.

**Status: research-quality photo/color study. Golden HOLD, no deploy, no branch merge.**
