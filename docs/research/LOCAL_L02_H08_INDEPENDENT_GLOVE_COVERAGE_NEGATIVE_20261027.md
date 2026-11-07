# L02 H08 independent glove coverage and watershed negative (2026-10-27)

**Research-only. REJECTED. Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD / production NO_GO.** No image, mask, private coordinate, human label, NPZ, or source pixels are stored in this repository. The known H08 case is exposed; this is not a blind-generalization result and not a current-main replay.

## Authenticated provenance and scope

- At this run's readback, GitHub main: `4a4348990084848c981811b414e6221411271f84`. This report is scoped to PR #445's A-only Draft branch, not main or production.
- Private reviewed evidence ZIP SHA-256: `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; its 19/19 internal manifest entries match.
- Private Run30 owner ZIP SHA-256: `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; its 7/7 internal manifest entries match.
- Private sleeve independent observer ZIP SHA-256: `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`.
- Signed H08 original encoded source SHA-256: `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`; frozen Run30 owner-array SHA-256: `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`. The observer class-id array SHA-256: `d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5`.
- This is a **Run30 baseline diagnostic**, not a reconstruction from current main. Human masks were used only for post-inference scoring.

## P0 root-cause isolation, not a threshold success

The frozen Run30 H08 owner retains 96,535 reviewed outerwear pixels and misses 60,035, with zero known false-owner pixels. Of those missing reviewed outerwear pixels, 48,343 have independent observer class32. Two large unassigned class32 8-connected components contain 28,231 and 22,894 source pixels. Together they include **48,159 reviewed outerwear pixels** and **2,310 known non-outerwear pixels**, plus unreviewed pixels. Both components touch *both* existing owner domains, so whole-component assignment, owner OR, or a simple connectedness rule is not a valid semantic repair.

The independent glove observation class18 covers only part of the dangerous class32 glove contamination: 1,656 known class32 false-owner pixels lie within 100px of class18, while **669 known false-owner pixels are farther than 100px**. The latter are in a separate glove-adjacent region where class18 does not supply a useful independent semantic veto. Thus class18 is **not a complete glove/arm observer** for this signed H08. A glove-distance gate cannot prove the absence of false owner additions.

## Frozen source-only negative candidate

A diagnostic candidate used 8-neighbor connected-component markers for both immutable owners, class18 as an independent competing glove marker, source RGB→OpenCV-LAB gradient watershed limited to class32/original owners/glove, then a source-only nearest-glove-versus-nearest-owner spatial-and-color veto. It removed newly introduced cross-owner contact and disconnected additions. No human label, polygon coordinate, generated pixel, or inpainting entered inference. Human labels were opened for postscore only.

| Signed H08 Run30 metric | Frozen before | Candidate after |
| --- | ---: | ---: |
| Reviewed outerwear true-owner pixels | 96,535 | 143,411 (+46,876) |
| Missing reviewed outerwear pixels | 60,035 | 13,159 |
| Known false-owner pixels | 0 | **1,429 (FAIL)** |
| Unknown pixels added | 0 | 630 (neither TP nor FP) |
| New source class32 owner pixels | 0 | 48,935 |
| Frozen owner erased / alpha-zero added / non-class32 added | 0 / 0 / 0 | 0 / 0 / 0 |
| Owner 1 4-neighbor components | 29 | **25 (FAIL, component merge)** |
| Owner 1 8-neighbor components | 22 | 22 |
| Owner 2 4-/8-neighbor components | 14 / 11 | 14 / 11 |

Candidate owner-array SHA-256: `0efe565f8adad9a254df34496a2d8a00c6b55513c232e31a9af5a25daa592ff7`. The improvement in known true-owner coverage **must not** be promoted: both arm/glove semantic ownership and 4-neighbor topology fail. No candidate code is integrated into a production path. No additional on-the-spot color/geometry threshold tuning is justified by this known-case result.

## Decisions and next integration gate

**Accepted P0 improvements 0, P1 improvements 0; H04/H06/H08 P0 cases remain unresolved (3).** This diagnostic establishes a specific blocker: the independent glove/arm evidence is incomplete, including a class32 glove-like region not covered by class18. Before an H08 large-sleeve recovery can be accepted, obtain independent source-only evidence that distinguishes that glove region from the class32 sleeve, preserve *both* 4- and 8-neighbor frozen component identities, and reject every new known arm/underlayer FP. The H06 underlayer/coat separation and H04 false-owner regression remain mandatory. Only then proceed to exact main-derived Phase4/5 replay, whole CI, signed unseen blind, and human Golden/iPhone review.

A private lossless owner, comparison visual and receipt were generated and locally SHA-verified. Upload to the established non-shared Drive evidence folder failed twice with `container_session_unavailable`; **cloud preservation/read-after-write is not verified**. No private artifact was uploaded to GitHub. Lane B, Public/C08, LocalWorker production and Golden were untouched.
