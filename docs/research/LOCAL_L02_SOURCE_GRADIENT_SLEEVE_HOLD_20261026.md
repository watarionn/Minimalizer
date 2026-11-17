# L02 source-gradient sleeve seam shadow, known signed H04/H06/H08 (2026-10-26)

**Research only. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** This is a sleeve-only *abstention* proposal, not a jacket/coat owner assignment. No production, B, Public/C08, Golden or acceptance changes.

## Problem and independent source-only hypothesis

The class32 sleeve candidate mixes real outerwear with H06's visibly separate white underlayer cuffs and H08's arm/glove area. A blanket OR/AND of class32 cannot separate them. A nearest-color palette also fails because source seed palettes include enough tones to match both materials. Instead, build 4-neighbour candidate connectivity using the original RGB's CIELAB76 *local edge* difference; anchor only to an independently inferred class5/10 seed. The edge cutoff is the **95th percentile of internal seed-to-seed differences on that same source**, not a per-character postscore threshold. All other candidate components abstain. This cutoff and method were examined on known H04/H06/H08, so no unseen-character claim is permitted. Human masks enter only the post-proposal evaluation.

## Actual signed-source replay (known-only, two deterministic passes)

The original embedded RGB/alpha bytes and source SHA were verified independently from the non-shared Drive reviewed archive; SegFormer class IDs, independent seed predictions and reviewed labels came from existing signed archives. No generated pixels, annotation-based inference or Golden replacement.

| Case | Raw attached-sleeve TP / known FP | New shadow TP / known FP | Arm FP before→after | Underlayer FP before→after | New shadow FN |
| --- | ---: | ---: | ---: | ---: | ---: |
| H04 | 49,386 / 4,423 | 49,053 / 3,844 | 784→205 | 2,091→2,091 | 3,519 |
| H06 | 291,088 / 11,551 | 289,621 / 5,065 | 225→0 | 11,326→5,065 | 25,202 |
| H08 | 144,836 / 2,362 | 144,620 / 448 | 2,362→448 | 0→0 | 11,950 |

These are comparisons against the **old, unsafe raw-attached sleeve union**, **not** current main's latest owner. Correct garment pixels also decrease by H04 333 / H06 1,467 / H08 216. H06 still misowns 5,065 underlayer pixels; H08 still misowns 448 arm pixels. The previously integrated H08 morphology candidate already achieved known arm FP **0**, so applying this shadow directly would regress that protection. **Do not merge as an owner quality fix.** All three P0 cases remain unresolved.

Candidate retained sleeve-only pixels: H04 14,995 / 15,972; H06 37,949 / 46,613; H08 49,408 / 51,634. Output byte hashes (bool→uint8 C-order): H04 `394ded02e8f876875abf6f44fcc2aae7fb839f8ca99950a2f7e30790d5a55610`, H06 `9d9911904952999045304176b9637a033a673595f973b51b373680ee44d8cdd7`, H08 `22c9753026298190ce2876c5e86a74db5aec573923aa3ceab4ded7e91a303aed`.

Source SHA-256: H04 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`, H06 `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`, H08 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`. Reviewed archive ZIP SHA `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`; Run30 ZIP SHA `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c` (historical comparison only).

## Gates

Seven isolated source-free tests PASS locally; exact committed blob and GitHub-head whole-repository CI require separate confirmation. Need source-only owner exclusivity/4- and 8-connectivity/critical-part retention, newest main-owner signed replay, H04/H06/H08 visual review, truly unseen signed blind character, and Golden/iPhone user acceptance before Phase5/production. This candidate **must not be wired into inference**, because sleeve-to-jacket-vs-coat ownership and remaining arm/underlayer errors are unresolved. P0 accepted fixes 0, P1 accepted fixes 0. Private images, masks, NPZ and coordinates stay only in the existing non-shared Drive evidence folder.

## 2026-10-26: signed H08 dual-owner contact, strict abstention (known-only)

**Critical P0 cause, not a quality fix:** the original source-gradient shadow retained
sleeve components that were simultaneously connected to frozen jacket and coat
seeds. Source RGB continuity cannot decide between those owners. A source-only
A research guard now requires an authenticated uint8 `seed_owner_ids` map
(0 outside seed, 1 for class5 jacket seed, 2 for class10 coat seed) and
abstains from every graph component anchored to **both** owner domains.
Missing, inconsistent, or mismatched seed ownership fails closed. It does not
infer ownership from human review, draw source pixels, or grant Phase4 PASS.

The signed H06/H08 original WebP bytes were independently decoded from the
existing non-shared reviewed archive; SHA-256 H06
`c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`,
H08 `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`.
The reviewed, Run30 and sleeve-observer archive SHA pins matched
`6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`,
`6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`,
`a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`.
Run30 4-neighbour owner/class seeds were reconstructed **without human masks**;
review masks were opened only after the proposal was frozen.

| Signed known source | Old source-gradient retained | New unambiguous retained | Dual-owner disputed | Known arm FP old→new | Reviewed garment TP old→new |
| --- | ---: | ---: | ---: | ---: | ---: |
| H06 | 37,949 | **37,949** | 0 | 0→0 | 29,607→29,607 |
| H08 | 49,408 | **61** | **49,347** (2 graph components) | 448→0 | **48,085→61** |

H08's 49,347 disputed pixels contain 48,024 reviewed true garment pixels,
448 reviewed arm pixels and 875 unknown/unlabelled pixels. This is **not**
a valid sleeve recovery: the strict guard prevents wrong owner promotion by
abstaining from almost the entire H08 sleeve candidate. H06 still retains
5,065 reviewed underlayer pixels in the *wrong garment hypothesis*; no
H06 cuff/coat semantic correction is achieved. The old/new proposals remain
research shadows and must **not** be connected to rendering.

H04 was **not** replayed in this addendum: its embedded signed source is
453×1400 while the historical Run30 owner is 796×796, and no new unverified
resizing/alignment was introduced. No H04 regression PASS is claimed.

The exact updated GitHub source blob and regression test blob were read back.
The local execution of those exact blobs passed **14 focused tests**, including
dual-owner contact, missing seed-owner evidence, class mismatch and source-alpha
negative cases. **Whole-repository CI, independent unseen signed blind,
Phase4 semantic quality, and latest-main complete owner replay remain
NOT_VERIFIED / FAIL.** Source-only H06/H08 checks do not replace those gates.

Accepted rendered-image P0/P1 improvements: **0/0**. Known unresolved
P0 cases H04/H06/H08: **3**. Keep this PR **Draft / unmerged**; the H08
48,024-pixel true-garment abstention makes it unsuitable for owner promotion.
Next meaningful P0 step is independent jacket-versus-coat sleeve-subpart
ownership evidence that preserves these genuine source pixels while excluding
the arm, not threshold tuning against the exposed review masks.
L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.
No Lane B, Public/C08, LocalWorker production, Golden, private originals,
NPZ or user annotation geometry was modified.
