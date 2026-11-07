# L02 H08 signed class32 component-majority negative (2026-10-29)

**Decision: REJECTED, P0 FAIL.** This is a known, exposed-character research experiment, not a Phase4 owner candidate, an unseen holdout, or a production implementation. No private source image, model mask, reviewed polygon, NPZ, source coordinates, or owner array is included.

## Verified provenance and baseline

- GitHub main independently read as `4a4348990084848c981811b414e6221411271f84`; A-only Draft PR #445 head before this note: `62b075cfc6b7ec53d751914cdda12eeb416b64da`. No main merge.
- Established **non-shared** Google Drive location: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`.
- Four independently materialized original private archives verified by SHA-256: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Reviewed/Run30/AnimeSeg member manifests 19/7/5 PASS.
- Historical 2026-10-23 **source-free** staging archive `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`, 98/98 members verified. Its source-only composed/strict owner reconstruction reproduced exact historical pins: H06 `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`; H08 composed `3e46769428946d54f0cc441ead77699a81839cd8e372ca39212e5b7825ee4a1a`, strict `32bb5266a479ce64571f190ffebe90b50c01329598408019b363c5ab0c9f0778`. **Not an exact-current-main or exact-PR-head full replay.**

## Source-only candidate frozen before human postscore

A single predetermined hypothesis was tested: fill only original opaque class32 unowned 8-connected components that (1) contain at least 200 source pixels, (2) have at least 50% generic AnimeSeg class10/11 support, and (3) touch the frozen coat owner2 within one 8-neighbour step. The proposal requires both owner1 and owner2 to be present; single-owner cases abstain. Newly assigned pixels may only be owner2, and 4/8 frozen component identity, source alpha, and new cross-owner contacts are fail-closed. New cross-owner contacts and component merges are pruned by source-only topology. This is **not** a claim that generic AnimeSeg class10/11 proves outerwear.

The fixed candidate implementation SHA-256 was `171a8e023ee7621f794e53555d43cd36e866f8b2bc3aec79522c249c3cc8c68d`. The complete source-only H08 owner was frozen at SHA-256 `68763cf42eb1fe5c6466a709b7d1704e3d0646020be68ff6f6e1e9f1c61ebcd3` **before** loading reviewed human labels. H06 candidate SHA equalled its strict baseline, no-op. No postscore-dependent threshold changes or second candidate were made.

## Actual signed known-case postscore

| Metric | H08 strict baseline | Component-majority candidate |
| --- | ---: | ---: |
| Reviewed true outerwear TP | 137,261 | 143,701 |
| Reviewed outerwear FN | 19,309 | 12,869 |
| Known non-outerwear FP | 0 | **667 (arm skin)** |
| Newly owned source pixels | 0 | 7,419 |
| New reviewed true / known arm / unknown | n/a | **6,440 / 667 / 312** |

The second-largest selected class32 component alone contributed **1,926 reviewed true garment pixels and 667 known arm pixels** (plus 108 unknown). This is direct evidence that a generic-clothes-majority **component cannot be safely promoted as a whole**, even when owner topology and source-alpha checks pass. Another large selected component added 4,471 reviewed true garment pixels and 204 unknown, but that does not rescue the mixed component or authorize postscore-informed component selection. Unknown is not a negative.

H06 remains 294,020 TP / 1,077 known underlayer FP / 20,803 FN, unchanged. H04 was not re-evaluated. **Candidate rejected** because 667 new known arm false owners violate P0. Do not ship, merge the experimental code, relabel unknown, or use human labels to select the safe-looking components. The local candidate is not part of PR #445.

## Integration and next gate

The next credible H08 step needs independent *positive* sleeve-versus-arm evidence within mixed class32 components, not a whole-component majority, simple class11 union, or colour-only subtraction. Keep current composed/strict baseline and prior 3,866-TP LAB-reach candidate separately identified; do not count this rejected experiment as an accepted improvement. H06's inherited frozen-owner underlayer 1,077px requires a separate, reviewed abstention contract.

**Accepted P0 0, P1 0; H04/H06/H08 unresolved 3.** No code PR, main merge, or Golden change from this experiment. Remaining gates: exact-main owner reconstruction and H04/H06/H08 regression; source-only Phase4 exclusivity/connection/critical parts; exact PR-head owner-PC QA; independent unseen signed blind cohort; Phase5 only after Phase4 PASS; human Golden and physical iPhone acceptance. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
