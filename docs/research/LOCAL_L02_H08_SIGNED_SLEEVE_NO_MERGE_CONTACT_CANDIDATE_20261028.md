# L02 H08 signed Run30 sleeve candidate with no-merge and current-main contact policy (2026-10-28)

**Research-only source-free candidate. No Phase4 or production approval.** All inputs are signed or externally pinned source/model/owner artifacts. No human polygons, reviewed labels, or postscore values entered the proposal. Reviewed masks were loaded only after the source-only output was frozen and SHA-256 hashed.

## Provenance and contract

- Exact main observed: `4a4348990084848c981811b414e6221411271f84`. PR #445 is Draft; no merge.
- Existing private Drive location: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence/`.
- Reviewed source ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 owner ZIP `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`; source-free 2026-10-23 staging archive `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`, manifest 98/98 matched.
- H08 source WebP SHA-256 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`; decoded RGBA SHA-256 `5107f0eeb3b950b8e93ceb3fb6f98c52ecf6e2ce94d39c1ee606f3fad1e8026c`; independent class map SHA-256 `d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5`; Run30 owner SHA-256 `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`.
- The candidate uses the original private **frozen attached-sleeve proposal** from the sleeve semantic archive, not a fabricated mask or an all-class32 union. The original H08 owner pixels remain immutable. Independent AnimeSeg generic-clothes class 10 gates additions; class 10 is **not** proof of outerwear.
- The new research-only module uses the current-main `propose_guarded_sleeve`, `prune_new_cross_owner_additions` and `audit_frozen_owner_transition` APIs, then independently checks 4/8 component identity and source/class eligibility. No production call site changed.

## Actual signed H08 Run30 comparison (postscore only)

| Metric | Frozen Run30 | Raw no-merge | Contact-pruned no-merge |
| --- | ---: | ---: | ---: |
| Reviewed outerwear true pixels | 96,535 | 116,710 | **116,566** |
| Reviewed outerwear missing pixels | 60,035 | 39,860 | **40,004** |
| Known non-outerwear false-owner pixels | 0 | 0 | **0** |
| New owner pixels | 0 | 20,249 | **20,105** |

The final 20,105 newly owned pixels comprise **20,031 reviewed outerwear** and **74 unlabelled/unknown** pixels. Unknown is not a negative or a proven positive. The no-merge stage first produced 21,503 additions, cut 1,254 unsafe join pixels, then the main-policy contact prune blocked **62 new 4-neighbour and 132 new diagonal contact edges**, removing 144 more proposed pixels and 0 frozen pixels. No new cross-owner contacts remained. Both owners' frozen component identities stayed one-to-one at 4 and 8 connectivity (jacket 29/22, coat 14/11 components). The output owner array SHA-256 is `ed2dec1c7d38f35a709e27968d02e635683315fb4fc0efb36976db6060e5617d`.

H04 and H06 Run30 regression with the exact frozen attached-sleeve candidate: **0 owner pixels changed**. Their inherited defects remain: H04 reviewed TP 49,386 / known underlayer FP 2,091 / arm FP 784; H06 reviewed TP 291,088 / underlayer FP 11,326 / arm FP 225. This candidate does **not** solve H04/H06 P0 defects. H08 remains visually incomplete; its remaining reviewed outerwear gap is 40,004 pixels.

The 2026-10-28 local source-free harness ran 4 targeted tests PASS for the new module. The current-main audit APIs and exact blobs were read through GitHub, but the local harness uses a compatible source-only mirror for these two audit APIs, **not a byte-identical local checkout of both main audit modules**. The contact and transition invariants were also independently recomputed on the actual H08 output. Thus this is **not** exact-main full replay, exact-PR-head CI, independent unseen-character generalization, or Phase4 semantic PASS.

## Decision

A **visibly meaningful H08 sleeve coverage research candidate** exists, but it is **not an accepted P0 fix**. H08 known-case postscore improved without labelled negative regression, yet unknown 74px, missing 40,004px, exposed-case selection, lack of unseen signed blind cohort and current-main complete stage reconstruction remain blocking. Source-only proposal code and tests are staged on A-only Draft PR #445; no B, Public/C08, production LocalWorker, Golden, signed originals, model weights, or user annotations changed.

**Accepted P0/P1 improvements: 0/0. Unresolved H04/H06/H08: 3. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** Next: exact current-main audited composed-owner replay and signed H04/H06/H08 regression with the new composition, independent unseen cohort, full CI, human visual and iPhone acceptance. Do not promote or merge this candidate while those gates fail.
