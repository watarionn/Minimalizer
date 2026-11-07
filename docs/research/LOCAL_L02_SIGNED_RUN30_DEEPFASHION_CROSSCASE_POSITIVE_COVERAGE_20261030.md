# L02 signed Run30: independent outerwear-positive coverage and cross-character false-owner risk (2026-10-30)

**Lane A research-only / exposed historical Run30 / negative gate.** This is an independently re-counted *set-overlap diagnostic*, not an executed owner proposal, an exact-current-PR replay, a new model inference, a blind holdout, or a Phase4 quality pass. No class allowlist, inference threshold, owner map, production code, Golden, or private input was changed.

## Authenticated inputs and procedure

- Canonical non-shared Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`.
- Independently downloaded and SHA-256 checked the signed reviewed originals ZIP (`6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, member manifest 19/19) and Run30 frozen owner ZIP (`6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, member manifest 7/7). The independent sleeve/class observation ZIP SHA was `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`. DeepFashion2 observer ZIP SHA was `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`.
- Used frozen Run30 4-neighbour owner masks and frozen DeepFashion2 outerwear predictions at their native archived 2000×2000 dimensions. First computed `independent_positive & ~frozen_owner` without reading human labels for any proposal. **No proposal or selection was made.** Afterwards used the existing reviewed masks for *postscore only*, with unknown pixels kept separate from known negatives. No human coordinates or masks were fed into inference.
- These checks authenticate archived bytes, **not** the original DeepFashion2 model weight bytes or the current PR head's full runtime.

## Cross-character diagnostic (pixels; historical Run30, not current strict)

| Exposed signed case | Frozen owner reviewed garment TP | Frozen owner known false owner | Independent DeepFashion2 positive outside frozen owner: reviewed garment | Known non-garment | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| H04 | 49,386 | 4,423 | 0 | 0 | 0 |
| H06 | 291,088 | 11,551 | **10,690** | **0** | **514** |
| H08 | 96,535 | 0 | **19,282** | **3,297** | **7,155** |

For H06, the 10,690 independently positive reviewed missing garment pixels include SegFormer class25 6,586, class30 3,437, and class0 667. This is *postscore class attribution only*: it **does not authorize widening class25/30/0 inference permissions** or selecting those classes using human labels. It identifies a potentially valuable source-only positive observer signal outside the historical class30/32-only recovery scope, while the 514 unknown pixels prohibit treating the signal as zero-risk.

For H08, a blanket DeepFashion2-positive owner union would include **3,297 explicitly known non-garment pixels** and 7,155 unknown pixels, even though it overlaps 19,282 reviewed missing garment pixels. That union is **REJECTED before implementation**. The H08 known false-owner region cannot be made safe by citing H06's zero observed known false pixels; cross-character behavior differs. H04 has no new positive coverage and retains 4,423 known false owner pixels.

The archived Run30 baseline is **not** the later composed/strict frontier: the separately documented historical strict H06 garment FN 20,803 and H08 FN 19,309 must not be compared as if the owner maps were identical. None of the numbers here are a measured improvement over strict, a current-main fix, or an unseen-character generalization result.

## Engineering consequence and gates

The next legitimate inference candidate must obtain **independent, affirmative outerwear-versus-underlayer/skin evidence** at subpart/pixel level, freeze its algorithm without using reviewed annotations as inputs, and preserve frozen owner exclusivity, 4/8 connectivity, critical limbs, and no new cross-owner contacts. An unqualified DeepFashion2 OR, class-based cherry-picking from postscore, negative-only AnimeSeg exclusion, and known-case threshold retuning are not acceptable. Run the current PR's exact source-only Phase4 gates, then signed source replay and visual comparison; do not claim a PASS from this diagnostic.

**Accepted P0 fixes: 0. Accepted P1 fixes: 0. Unresolved H04/H06/H08: 3. PR #445 stays Draft; no merge. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Physical iPhone QA remains a *post-deployment acceptance* activity, never a pre-deployment GO blocker; no owner acceptance was performed.
