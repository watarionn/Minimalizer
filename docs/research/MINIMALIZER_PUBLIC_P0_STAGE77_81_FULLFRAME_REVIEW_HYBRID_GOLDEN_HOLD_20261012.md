# MinimalizerPublic StructuralRecovery P0 Stages 77–81: full-frame review queue, untrusted semantic drafts, byte-compact source-color SVG

Date: 2026-10-12. Research-only on Draft PR #390 `watarionn/Minimalizer`. **Never merge or deploy until human Golden and release gates independently pass.** No generated pixels or inferred semantic foreground. No change to main, regular Public conversion, Stage51 live research preview, or Local Minimalizer.

## Stage77: complete original-frame source-only review inventory

Module `web/static/public-fullframe-review-p0.mjs` repins original 340x340 GC001/Raden RGBA plus historical left/right source candidates, face mask, and the *unapproved* background observation. A worklist partitions **all original source pixels**, not only previous historical "arm" masks, into 32x32 tiles. Original-source RGB adjacency counts are **diagnostic**, not human anatomy or background segmentation.

| Original | Frame pixels | 32px review tiles | Original alpha=255 | Other alpha | Strong 4-neighbor RGB edges | Historical candidate pixels | Opaque outside historical candidate |
|---|---:|---:|---:|---:|---:|---:|---:|
| GC001 | 115,600 | 121 | 115,152 | 448 | 24,434 | 9,160 | 105,992 |
| Raden | 115,600 | 121 | 115,152 | 448 | 15,568 | 20,177 | 94,975 |

**Caution:** opaque does NOT mean foreground; opaque-outside-historical includes original-background pixels. A list of 121 tiles does NOT mean anyone inspected them. GC001/Raden remain **0 independently human-reviewed semantic pixels**, with no approved source silhouette, neckwear, hair, sleeve or skin.

## Stage78: full-frame manual draft contract, no automatic truth

New `MinimalizerPublic-P0-fullframe-review-draft-v1` RLE contract admits untrusted observations on any original opaque pixel (including face and outside old owner masks) with codes: unreviewed, background proposal, hair proposal, face proposal, skin proposal, sleeve proposal, garment proposal, neckwear proposal, accessory proposal, uncertain subject. Original source RGBA SHA256, pinned original PNG identifier, SHA-recomputed historical-source eligibility mask, case and dimensions must agree. Nonopaque labeling, invalid RLE, altered source, forged reviewer authentication or `approved=true` are denied. A draft is always `UNTRUSTED_FULLFRAME_DRAFT_HOLD`; it cannot repaint source RGB or establish reviewer identity. No real human draft was submitted; test annotations are synthetic.

## Stage79: independent-source dual proposal disagreement / HOLD

Each of two untrusted proposals is validated **separately** against independently supplied original bytes; duplicate identical draft hashes are rejected for purposes of pretending to have two independent reviews. For distinct valid drafts, the comparator reports agreement/disagreement/abstentions and bounded ambiguous original-pixel indices, without assigning human identity or promoting a class. **No actual reviewer receipts for whole frame or human Golden**. `fullFrameGoldenGate` is fail-closed even if untrusted caller supplies `approved` fields.

## Stage80: exact orthogonal source-contour vs Stage73 fill competition

`web/static/public-source-compact-hybrid-p0.mjs` derives **actual source-pixel medoid color layers**, independently pinned by Stage68+73 original source SHA checks. For each layer, try Stage12 4-connected pixel-edge rings with an even-odd hole rule and compact H/V/h/v SVG path serialization. The Stage12 routine raster-proves every source-mask pixel exactly. Compare **actual UTF-8 SVG fragment bytes** against Stage73 exact rectangular fills, select strictly smaller, otherwise preserve Stage73 exact geometry unchanged. No contour simplification, inferred silhouette, partial alpha, pixel/color extrapolation, or full-image replacement.

Actual original GC001/Raden private replay:

| Historic source mask (not human-certified anatomy) | Stage73 fill SVG bytes | Stage80 selected SVG bytes | Byte saving | Selected geometry vertices |
|---|---:|---:|---:|---:|
| GC001 left_arm | 12,396 | 9,808 | 2,588 (20.9%) | 2,626 |
| GC001 right_arm | 23,528 | 17,746 | 5,782 (24.6%) | 5,356 |
| Raden left_arm | 52,469 | 40,323 | 12,146 (23.1%) | 11,640 |
| Raden right_arm | 36,661 | 26,866 | 9,795 (26.7%) | 8,420 |
| **Total (isolated 4 mask SVGs)** | **125,054** | **94,743** | **30,311 (24.2%)** | **28,042** |

All real original 4 owner color candidates × **actual Google Chrome 340px and 680px**, 8 render proofs: **0 missing pixels, 0 extra pixels, 0 wrong RGB and 0 fractional-alpha**. Independent deterministic original-source re-derivation of each SVG passes. Private Chrome screenshot PNG, candidate SVG and original SHA evidence are **Drive-only**.

**Do not conflate** isolated colored source-mask polygon path vertices with the **entire-character** vertex budget. Historical Stage8 total GC001 3,604>1,887 and Raden 2,370>1,412 still FAIL. Sum 28,042 selected color layer vertices (for only historical owner candidates) cannot meet full-scene cap either. Smaller XML or source-pixel exactness says nothing about missed arms, miscolored ties, bad body Golden or person/background semantic separation.

## Stage81: source-only regression, CI, archival and release veto

Added `tests/js/test_public_fullframe_stage77_81_p0.mjs` (29 new Node tests at initial authoring), plus Stage77–80 research modules and CI workflow registration. Regressions include source/face/historical-owner SHA, fullframe coverage and alpha, untrusted metadata, false review signing, duplicated drafts, disagreement, source RGB, deterministic selected SVG geometry, path injection and fail-closed release. **Actual GitHub Actions verified:** [run 38201062990](https://github.com/watarionn/Minimalizer/actions/runs/38201062990), job 114654366434 on executable/test SHA 8e6dce0517915ccdea2f58305a2361afceec927e, decoded runner log **442 passed / 0 failed / 0 skipped** (413 earlier + 29 new). See `MINIMALIZER_PUBLIC_P0_STAGE81_CI_442_PASS_GOLDEN_HOLD_20261012.md`.

Remaining blocks: 0 real authenticated whole-frame semantic labels; no independent two-reviewer human identity, adjudication, silhouette/face/sleeve/arm/neckwear/hair Golden; no whole-scene shape budget, full-character production-quality E2E, real Public HTTPS/iPhone Safari test or validated rollback. Normal product and Local remain unchanged; PR must remain Draft/HOLD.

Canonical Drive folder: `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage77_81_20261012`. Source RGBA, original PNG/masks, real selected SVG, 8 Chrome PNGs, private replay scripts and logs stay **PRIVATE Drive-only**, never public GitHub.
