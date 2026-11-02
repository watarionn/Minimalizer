# L02 H08 class32 sleeve positive-evidence shadow (2026-11-02)

**Research-only / NOT an exclusive owner repair.** H04/H06/H08 are exposed known cases. No new model inference, no independent semantic observer, no unseen blind, no Phase4 admission, and no Golden approval. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## Why this matters

Run30 H08 has 51,634 ambiguous class32 sleeve pixels, including 48,301 reviewed outerwear, 2,362 known arm and 971 unknown. Blanket OR adds arm; blanket AND loses sleeve. The existing PR #449 H06 abstention can remove false owner pixels but cannot restore H08's missing sleeve. This new **positive-evidence-only** shadow tests whether signed-source color can separate likely sleeve from arm while refusing to assign either exclusive owner.

## Frozen source-only rule

- Inputs: exact signed H04/H06/H08 source RGB/alpha, Run30 4-neighbour frozen class IDs and exclusive owner; three SHA-256 values must match the independently pinned registry in PR #449. No human annotation, mask, coordinate or postscore is accepted by the inference function.
- Garment seeds are class5/10 pixels already owned by frozen owner 1/2. Competitors are class2 and class7 source colors. CIELAB medians are computed from these predictions and original RGB. The garment radius is the 95th percentile of seed distances. Only alpha-positive, currently **unassigned** class32 pixels within this radius and strictly closer to garment than 0.60 times the nearest competitor distance become **positive evidence**, not owner pixels.
- Fixed research constants are not per-character retuned after postscore. This is source-color evidence from the same frozen SegFormer taxonomy, **not an independent model**. Owner output remains byte-identical to Run30. Unknown pixels are not negative.

## Actual signed-image replay and independent postscore

The source-only proposal was frozen and run twice before human visible labels were loaded for evaluation. Two runs gave identical masks and receipts for each signed case. Values below are known-case postscore, not a blind result:

| Case | Unassigned class32 target | Positive evidence | Reviewed outerwear | Reviewed arm | Reviewed underlayer | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H04 | 326 | 6 | 0 | 0 | 0 | 5 |
| H06 | 50 | 0 | 0 | 0 | 0 | 0 |
| H08 | 51,691 | **31,505** | **30,978** | **38** | 0 | **489** |

H08 mask SHA-256 `1f2415cbaf04e146582d41eedad1ca72e3e18963fe5ac14ca4700c658703bcb8`. Private source-overlay visual was inspected: the evidence highlights substantial portions of the pink sleeves, while 38 reviewed arm pixels still leak through. The evidence does not establish jacket-vs-coat owner identity, layer order, connectivity, or acceptable whole-character appearance. **No P0/P1 fix is admitted.** H06's 208 correct-coat-pixel erasure in the other #449 candidate is unchanged.

## Source and preservation

- Canonical private Drive source ZIP SHA-256: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; Run30 owner `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`. The three archive bytes were retrieved from the existing non-shared Drive and independently SHA-checked.
- A deterministic private ZIP with candidate NPZ masks and H08 source overlay was locally built and its six internal entries checked; SHA-256 `9827b6704bda2bd61faeb27940906a2263d9ebdfdb079be15719b183369ac9a8`. **Canonical Drive upload returned `container_session_unavailable`, so this new ZIP is NOT cloud-preserved and must not be counted as a shipped private artifact.** No raw source, mask, NPZ, image, or coordinates are committed to GitHub.
- The new module's exact Git blob and fail-closed source-free tests are in PR #449; isolated tests 4/4 PASS. This is not full exact-head repository QA or model licensing clearance.

## Next quality gate

Obtain a genuinely independent positive garment-vs-arm observer (SCHP-ATR18 in PR #447 is still model-download blocked and does not itself distinguish coat from underlayer). Require frozen owner 1/2 assignment with zero known critical-part loss, owner exclusivity, 4/8 connectivity and cross-owner contact, exact-head QA, and truly unseen signed blind before Phase4 promotion. Keep H04/H06/H08 unresolved=3, accepted P0=0/P1=0, Draft unmerged. B L04/L07, Public/C08, LocalWorker production and Golden remain untouched.
