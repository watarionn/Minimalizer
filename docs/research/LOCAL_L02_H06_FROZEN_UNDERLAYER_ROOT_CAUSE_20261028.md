# L02 H06 inherited frozen-owner contamination: signed root-cause gate (2026-10-28)

**A-only source-free diagnosis; P0 unresolved.** This is an exposed H06 known case, not an unseen holdout, an owner correction, or a Phase4 quality PASS. No source image, human mask, private NPZ, coordinates, or derived owner pixels are included.

## Verified inputs and reproducibility boundary

- Direct GitHub read: main `4a4348990084848c981811b414e6221411271f84`; PR #445 A-only Draft head at investigation start `50b0f783ef2bd90574207c145db9fd35af867247`.
- Established non-shared Drive `chatGPT及びCodex用/Minimalizer`, nested `10_Artifact_Library/03_Private_Research_Evidence`. Exact private SHA-256 matches: ReviewedEvidence `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; SleeveSemantic `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`; AnimeSeg offline384 `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Private member manifest checks: 19/19, 7/7, 5/5.
- Authenticated source-free staged archive `LaneA_L02_20261023_2253_SelectiveSignedOptIn_Integrated_SOURCEFREE.zip` SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`; 98/98 manifest entries match. Its isolated tests: 235 passed, 31 subtests passed. **Not exact current-main, exact PR head, or full CI.**
- Actual signed H06 canonical composed/strict replay reproduced SHA-256 `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`. Source-only proposals were computed before the reviewed human labels were opened. This is the **historical staged pipeline**, not a complete current-main reconstruction.

## P0 root cause: remaining underlayer FP cannot be repaired by additive-only stages

| Signed H06 reviewed-only | Frozen Run30 owner | Composed P0 / strict owner |
| --- | ---: | ---: |
| Correct outerwear TP | 291,088 | 294,020 |
| Known underlayer false owner | 11,326 | **1,077** |
| Known arm false owner | 225 | **0** |
| Remaining outerwear FN | 23,735 | **20,803** |

All **1,077** residual underlayer FP pixels are **already assigned to owner2 in the frozen Run30 owner**, all from SegFormer class32. **Zero** of those 1,077 were newly added by the composed P0 stage. The composed stage removes 10,249 earlier underlayer FP, but cannot remove the final 1,077 while its frozen-owner immutability contract remains in force. The remaining 1,077 are split across 11 eight-connected regions, dominated by 820/212/33 pixels. Therefore additional class32 owner reach, OR/AND, contact pruning of *new* additions, and LAB sleeve extension **cannot resolve this H06 P0 defect**. Do not claim H06 P0 resolution from an additive-only stage.

## Independent-observer ambiguity (diagnostic, not a veto)

Among the 1,077 known residual underlayer FP, AnimeSeg class11 accounts for 1,049, class10 for 17, other for 11. But among **31,066 correctly owned reviewed class32 outerwear pixels**, AnimeSeg class11 still accounts for **8,344** and class10 for **20,701**. Thus a blanket `class32 & anime11` subtraction would also remove substantial correct outerwear. It is **not a valid underlayer classifier**.

A separate existing Drive DeepFashion2 outerwear archive was also examined as **exploratory, not externally pinned independent authority** (locally computed archive SHA-256 `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`). Its prediction covers **0/1,077** residual known underlayer FP but only **311/31,066** correctly owned class32 outerwear pixels. Absence of DeepFashion2 support is therefore **not evidence of underlayer**. Using it as a negative veto would erase many true sleeve/coat pixels. The source-only inference pipeline must not ingest reviewed human labels.

## Required next engineering decision

1. Treat the final 1,077 frozen class32/owner2 underlayer pixels as a **separate pre-existing frozen-owner semantic correction problem**, not as missing sleeve additions. Any change that abstains from a frozen owner requires independently authenticated, source-only *positive* underlayer-vs-coat evidence and an explicitly reviewed allowed-abstention contract. Never use known human labels as inference coordinates or silently loosen frozen-owner gates.
2. For any candidate, freeze its source-only owner SHA **before** opening reviewed labels, then check H06 known underlayer FP, 31,066 class32 true coat preservation, known arm, all reviewed positives, 4/8 component identity and cross-owner contacts. H04/H08 must be independently regressed; unknown pixels remain unknown.
3. Reconcile historical staged modules with exact current-main owner reconstruction, then exact PR-head CI and a genuinely unseen signed cohort. No Phase5 until Phase4 owner exclusivity, connectivity and critical-part preservation are quality PASS.

**Decision:** Accepted P0 improvements 0; P1 improvements 0. H04/H06/H08 P0 unresolved 3. Code repair 0; this document is an audit-only integration artifact. PR #445 stays Draft/unmerged. `L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO`. No Lane B, Public/C08, production LocalWorker or Golden changes.
