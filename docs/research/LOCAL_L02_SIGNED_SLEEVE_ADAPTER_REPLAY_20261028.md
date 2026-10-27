# L02 signed sleeve adapter and authenticated known-case replay (2026-10-28)

**Lane A source-free integration evidence. Research-only, NOT Phase4 quality approval.** Main was independently read at `4a4348990084848c981811b414e6221411271f84`; PR #445 remains Draft/unmerged. No Lane B, Public/C08, production LocalWorker, Golden or human references were changed.

## Actual input and archive checks

- Canonical private Drive: `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence`. Source-free staging archive from the existing Drive folder SHA-256 `c442c661c10b74fbeaa98c84c077466cfaef50421abbfa2b5aa645268b1560bc`, internal manifest **98/98**.
- ReviewedEvidence private ZIP SHA-256 `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, internal **19/19**. Run30 private owner ZIP SHA-256 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, internal **7/7**.
- H08 encoded original WebP SHA-256 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`; decoded RGBA `5107f0eeb3b950b8e93ceb3fb6f98c52ecf6e2ce94d39c1ee606f3fad1e8026c`; SegFormer class IDs `d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5`; frozen Run30 owner `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`.
- H08 AnimeSeg class map SHA-256 `9f831bfd08895e78e7784f1f59de48437307764f9de7ed95b0c548b294085a69` from the existing offline384 private ZIP (internal **5/5**). H08 attached-sleeve frozen candidate bool-array SHA-256 `5330abb3927ffdeeccf450f9785153d37b31f74492c3cd53ea347de567512fdb` from the existing private SleeveSemantic ZIP. These two **array digests were newly observed during this run**. The archive provider was authenticated, but independently pre-established external ZIP pins for both archives were not established. Do not claim an independently authenticated unseen replay.

## New source-only integration

`tools/research/local_l02_sleeve_signed_source_adapter.py` authenticates supplied encoded source bytes, independently decoded RGBA, SegFormer IDs, AnimeSeg IDs, frozen sleeve candidate and frozen owner before calling the existing `local_l02_sleeve_contact_safe_shadow.py`. It rejects missing/mismatched digests, invalid shapes and classes, source decode mismatch, missing frozen candidate coverage, input mutation, output aliasing, frozen owner erasure and source-alpha escape. It **does not establish that a caller obtained pins independently**. The receipt explicitly sets `external_pin_provenance_verified=False` until a separate independently authenticated manifest verification step exists.

`tests/test_local_l02_sleeve_signed_source_adapter.py` supplies source-free valid and negative cases. **9/9 tests PASS in an isolated archive-backed mirror**; this mirror uses the historical source-only contact implementation, not the exact PR head and exact-main audit blobs. The two committed Git blobs were read back and matched the local tested bytes. Full PR CI remains unverified.

## Signed H08/H06 replay, known cases only

The adapter was run locally with authentic H08 and H06 source, class, AnimeSeg, attached sleeve candidate and Run30 owner arrays. The local isolated replay used the historical source-only no-merge/contact implementation; the actual PR sleeve implementation was not executed byte-for-byte in this environment. H08 output owner SHA-256 `ed2dec1c7d38f35a709e27968d02e635683315fb4fc0efb36976db6060e5617d` **exactly matches the already recorded H08 candidate**. H06 remains a no-op with owner SHA-256 `4be9ae240b8d32cc6b0923371f5c5b3a6159196ba819aa0b7044c06740a7b317`.

| Known-case metric | Run30 | Contact-safe H08 candidate |
| --- | ---: | ---: |
| H08 reviewed true outerwear | 96,535 | 116,566 |
| H08 reviewed missing outerwear | 60,035 | 40,004 |
| H08 known non-outerwear false-owner | 0 | 0 |
| H08 added owner pixels | 0 | 20,105 |
| H08 frozen owner erasure | 0 | 0 |

These are **reproductions of a previously exposed known-case candidate, not newly accepted P0 improvements**. H06 unchanged: reviewed true outerwear 291,088, known false-owner 11,551, missing 23,735. H04 was not rerun. No new blind character was available. Labels were used **only after the output had been frozen** for scoring; no human annotations or coordinates entered inference.

## Ship / remaining gates

Two source-free code/test files added to A-only Draft PR #445. No merge and no production changes. Accepted P0/P1 improvements **0/0**, unresolved major cases **H04/H06/H08 = 3**. No new private candidate archive was uploaded; Drive read-after-write for this run is **not established**. Do not treat local temporary arrays as preserved private evidence.

Next: independent external pins for AnimeSeg and attached-sleeve candidate archives; exact-PR-head and exact-main contact/transition audit replay; full current-main dependency closure (at least 11 remaining modules, subject to fresh audit), H06 underlayer/coat semantic repair, H08 remaining 40,004px, H04 regression, unknown signed blind, CI, owner Golden and iPhone acceptance.

**L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**
