# H08 signed non-class32 owner rescue: semantic negative (2026-10-25)

**Lane A L02, known-case-exposed, REJECTED. No owner promotion, no production change.** This records a substantive visual-quality failure of a plausible source-only rescue, not a benchmark PASS or new release gate.

## Source and frozen baseline

The four private canonical archives were materialized from the existing non-shared Drive `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence` and SHA-256 verified: reviewed `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, sleeve observer `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Manifest checks: reviewed 19, Run30 7, AnimeSeg 5. Original RGBA source SHA matched the private signed review audit.

The established source-only chain was reconstructed, with exact stage hashes: composed `3e467694...`, strict `32bb5266...`, single-anchor `6472cfc4...`, class32 palette `f847f995...`, and current H08 composed owner **`94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`**. Frozen baseline known-only score: TP 144,221 / known FP 17 (arm 17) / FN 12,349.

## Frozen source-only probes and independent postscore

An explicit *non-class32* rescue considered SegFormer classes **0/2/7** only where the independent AnimeSeg observer predicted generic clothes (class10), original alpha was nonzero, and the **existing adopted** source-color palette gate accepted the RGB. No human labels, coordinates, masks, or postscore were inference inputs. Connected additions were assigned to immutable source-owner components using nearest-seed partition and 4-neighbour reachability; component identity and cross-owner contact gates were checked.

- Initial direct source-only growth: 22,406 added original-source pixels, 2,736 reviewed outerwear TP, **19,670 unknown**, 0 known FP; **rejected for component topology failure**. Frozen owner SHA `14c7de82c16e0b6ff70302603a752b7d8d16945ec1e4a93ec81493333b13d6a3`.
- Component-safe partition: 21,209 added pixels, 2,661 reviewed outerwear TP, **18,548 unknown**, 0 known FP, invariant checks passed; frozen owner SHA `ff2a7b8a303a17af3de58904729ba27dbcc658cc012b2e1b2ea7f543b8b9fecb`. **Private original-RGB visual comparison rejected this result:** the additional material substantially fills the character's black inner top between jacket panels, not just the missing outerwear. Known-only IoU improved from 0.921028 to 0.938022, but that metric **did not reveal the semantic error**. Unknown is not a negative and must not be relabelled merely to change the score.
- A separate source-alpha **exterior-boundary** component restriction (no human mask or tuned distance) yielded only 205 additions: 101 reviewed outerwear, 104 unknown, 0 known FP; frozen SHA `379358ffe495077f145366f2acf2e7217dca3435ab2a9d69313561a1892852b5`. Insufficient visible P0 improvement; rejected.
- A separate class32-only source-color/AnimeSeg source proposal added 14 reviewed outerwear pixels, 0 known FP, 0 unknown; frozen SHA `6f44ed9bcdf01912c82d1b898d0edba4f233a825dd355c926ff0dd836e1afc6d`. P2 only; backlog, not a quality milestone.

All proposals were frozen/hashed **before** reading human review masks. Only the original signed RGB/alpha supplied pixels; no img2img, generation, inpainting or face feature rendering. Private arrays, visual boards, source pixels and review coordinates remain outside GitHub.

## Engineering decision

**Do not extend the allowed owner classes to 0/2/7 on generic-clothes and color evidence alone.** The black inner top is a concrete P0/P1 semantic owner trap. This also demonstrates why known-only FP=0 and improving IoU cannot substitute for full-frame visual review or an independent garment-specific observer. The existing source-only class policy remains unchanged; no model or thresholds were altered. Investigate independent garment-versus-inner-top evidence rather than adding a new heuristic tuned to these known characters.

**Accepted P0 resolved 0 / P1 resolved 0; H04/H06/H08 remain unresolved.** No code change in this negative run. Draft PR #439 and #440 remain unmerged; whole-repository CI, signed unseen blind, Phase4 owner quality and Golden remain pending. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No Lane B, Public/C08, production Worker or Golden changes.
