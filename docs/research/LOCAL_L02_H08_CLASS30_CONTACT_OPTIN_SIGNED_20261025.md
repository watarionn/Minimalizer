# Lane A L02: signed H08 class30 contact + palette opt-in (2026-10-25)

**Research-only, known-case-exposed. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Goal and mechanism

The previously merged PR #430 source-only contact-density/palette research was limited to SegFormer class32. This opt-in expands candidate eligibility to classes **30 and 32**, without modifying original model observations, frozen owners, color-trusted seed policy, or existing default class32-only behavior. The same >=1024 connected-candidate, >=10% frozen-owner contact, >=32 independent AnimeSeg generic-clothes support, RGB/LAB palette and 4/8 topology/cross-owner-contact gates apply. Model classes 30/32 are **not** semantic truth. This is a narrowly scoped A-only research option, not a production classifier.

## Independent signed-source replay

Canonical non-shared Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/`. Authenticated original source RGB/alpha, SegFormer/AnimeSeg and Run30 owner observations from four pinned ZIPs. ZIP SHA-256 pins and member manifests were verified (reviewed 19, Run30 7, AnimeSeg 5). The H06 composed and H08 single-anchor/#430 source-only baselines were independently reconstructed with pinned owner SHA-256 before proposals. **Both candidate arrays were frozen before opening any human evaluation labels.** Two identical replays produced the same source-free log SHA-256 `c712598cf96e54fe91a1d05273918445e933b67ed3c56b2f5403991ee11e042b`. The JSON-only aggregate SHA-256 is `be486a9982ae564336391b82ae20aa0be62c0fe4c413b9779821d13c826d8e8b`.

| Exposed signed case | Baseline TP / known FP / FN | Opt-in TP / known FP / FN | Added TP / known FP / unknown |
| --- | --- | --- | --- |
| H06 | 294,020 / 1,077 / 20,803 | unchanged | 0 / 0 / 0 |
| H08 | 143,372 / 17 / 13,198 | **144,221 / 17 / 12,349** | **+849 / 0 / +5** |

H08 known-only IoU **0.915606 -> 0.921028**. Source-only 4/8 component identity, frozen-owner immutability, source-alpha confinement and cross-owner contact checks passed. A private image crop showed a small but visible added garment region near the shoulder/sleeve. The **17 known arm FP remain** and **12,349 reviewed garment pixels remain missing**. Five new pixels are unlabelled/unknown, not negative or confirmed correct. No newly signed unseen character was evaluated. H04 was not rerun, and this does not establish a global quality gain.

**Run delta: 1 previously unresolved P0 case (H08) partially improved by 849 reviewed true garment pixels, 0 P0 fully resolved, 0 P1 independently verified, 3 P0 cases still unresolved.** This is a smaller gain than PR #430's previous +5,583px and is not counted as another resolution. No threshold was optimized against H08 human labels; the fixed prior policy was reused with the class30 eligibility hypothesis. Known cases are exposed and cannot count as blind generalization.

## Integration boundary

- Opt-in argument `eligible_classes=(30,32)` is accepted only by dormant `tools/research` modules. Existing default `(32,)` remains unchanged.
- Source-free negative/invariant tests cover default no-op on class30, opt-in recovery, unsupported class policy rejection, alpha/owner preservation; 29 focused tests plus 258 L02 source-free tests and 31 subtests passed in the local research overlay. This is not full GitHub repository CI, which has no run record for this PR.
- No private images, masks, NPZ, annotation coordinates or source bytes in GitHub. The source-free aggregate is the only public replay artifact.
- Phase4 owner exclusivity, semantic correctness, critical-part retention, and connection still FAIL globally. Unknown signed blind, Phase5 and user Golden/iPhone acceptance remain pending. B L04/L07, Public/C08, production LocalWorker and release untouched.
