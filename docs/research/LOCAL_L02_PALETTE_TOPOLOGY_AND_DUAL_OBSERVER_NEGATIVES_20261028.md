# L02 signed Run30 palette/topology and independent-observer negatives (2026-10-28)

**A-only source-free evidence; not an accepted quality fix.** Historical Run30 owners are already frozen. No private source pixels, human masks, NPZ, image exports, annotation coordinates, or model weights appear in this file. `L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO`.

## Provenance and reproducibility boundary

- GitHub main independently read: `4a4348990084848c981811b414e6221411271f84`; PR #445 is Draft and unmerged. The experiment did **not** reconstruct a current-main composed owner.
- Canonical non-shared Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`.
- ZIP SHA-256 rechecked against independently published pins: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30Owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`. ReviewedEvidence 19/19 and Run30 7/7 internal member hashes matched. Signed encoded original PNG SHA pins for H04/H06/H08 matched the existing source-free ledger.
- DeepFashion2 independent-observer ZIP was retrieved and locally SHA-256 checked as `f8240a4c71ec9c11142cfc1cd281e5d7c8f36e2b5b015b50132e92b785b03491`; **an independent external ZIP pin was not established in this run**. Do not use that observation for an approved candidate.
- No human masks or annotation coordinates entered either proposal. The known human masks were opened **only after** owner proposals had been frozen for postscore. Unknown is not negative.

## Candidate A: source-derived coat/jacket palette veto with topology repair, rejected for frozen-owner use

One fixed, exposed-case research hypothesis: fit 8 deterministic OpenCV-LAB prototypes to source-alpha-opaque, class5/10 owner seeds; set a 99.5th-percentile seed-distance outlier limit; abstain on class32 owner pixels beyond that limit. Restore minimal corridors **within the original owner only** to preserve 4-connectivity, without generating pixels or reassigning owners. These are exploratory choices, **not blind-calibrated thresholds**. Deterministic second replay matched the first byte-for-byte.

| Signed known case | Run30 TP / known FP / FN | Candidate TP / known FP / FN | 4/8 components | Existing owner pixels erased |
| --- | --- | --- | --- | ---: |
| H04 | 49,386 / 4,423 / 3,186 | 49,313 / 4,059 / 3,259 | 5/5 → 5/5 | 437 |
| H06 | 291,088 / 11,551 / 23,735 | 290,800 / 6,001 / 24,023 | 9/8 → 9/8 | 5,985 |
| H08 | 96,535 / 0 / 60,035 | unchanged | unchanged | 0 |

H04 loses **73 reviewed true garment pixels** while removing 364 known false-owner pixels. H06 loses **288 reviewed true garment pixels** while removing 5,550 known false-owner pixels; 147 removed pixels are unknown and must not be scored as negatives. Source-only owner SHA-256: H04 `8adcff9b89439c11fe72c56772779563ce044eddd24e543da54df144c6f07d59`; H06 `b342b22e7876568c778e7ea518bec173d04f3a50f9c8249234e178634acda217`.

**Critical blocker:** the authoritative main `audit_frozen_owner_transition` rejects deletion of frozen owner pixels without independently preapproved abstentions. These 437/5,985 erasures are **not** preapproved. Topology preservation does not waive frozen-owner integrity, and a candidate may not approve its own abstentions. Therefore **REJECT for PR merge/current frozen-owner integration**, even though some known false-owner pixels decrease. The underlayer/coat distinction is still incomplete and visible P0 quality is not PASS.

## Candidate B: independent DeepFashion2 ∩ class32 dual-owner Voronoi, rejected

A separate one-shot source-only H08 proposal required class32, independent DeepFashion2 outerwear, source alpha, and a 5-pixel nearest-owner distance margin. New 4/8 component counts stayed unchanged, but of **2,239** added H08 pixels only **1,567** were reviewed true garment; **660 were known false-owner** and 12 unknown. H06 remained unchanged. **REJECT** for arm/underlayer regression and incomplete independent ZIP pin. No threshold retuning to rescue the exposed H08 result.

## Decision, preservation and next gates

The visual comparison still shows H06 underlayer/cuff confusion and large H08 sleeve loss; neither experiment establishes an accepted P0 or P1 improvement. **Accepted P0 = 0, P1 = 0; H04/H06/H08 unresolved = 3.** No source code activated, no PR merge, no main change. The current-main audit contracts and full exact-head CI have not passed for these proposals.

A private candidate/visual/receipt ZIP was assembled and internally SHA-checked locally (SHA-256 `808c935a05101c5a0aca28c2e8cf1b61c08bf37d0f85f11818025eee59aec031`), but its upload to the existing non-shared Drive folder returned `container_session_unavailable`. **Cloud preservation and read-after-write are NOT verified.** Do not call that private archive durable.

Next: reconcile pre-freeze semantic class32 abstention with the frozen-owner contract rather than self-authorizing erasures; restore the 12 missing current-main composed-replay dependencies with exact audit version pins, independently verify signed H04/H06/H08 P0 retention and 4/8 connectivity, and require an unseen signed blind cohort before quality promotion. Source-only Phase4 owner/critical-part quality, Phase5, full CI, Golden and physical iPhone acceptance remain blocked. Lane B, Public/C08, production LocalWorker and Golden were untouched.
