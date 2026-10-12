# MinimalizerPublic StructuralRecovery P0: Stages96–105 private review readiness and original-opacity diagnostics
2026-10-13 JST; `watarionn/Minimalizer`, research Draft PR #390 only. **Golden HOLD**, no main/Local/ordinary Public/Stage51 edits, merge or deployment.

## Stages96–99: real human review readiness, not artificial review
`public-human-review-protocol-p0.mjs` consumes two **independently SHA pinned originals** GC001 and Raden, packages exact per-case source RGBA/PNG SHA, review packet SHA, full original source pixel and tile accounting, and mandatory human checklist: silhouette/person-background, arms/hands, skin/sleeve, hair/fine strands, collar/necktie, garments/small details, face suppression.
- Stage96: two-case complete reviewer manifest; signed original pixel coordinates only, no fabricated manual mask.
- Stage97: untrusted draft **syntactic** pixel coverage across the entire source opaque area, explicitly not authentic semantic quality or human identity. Reports number still unreviewed.
- Stage98: all original tiles prioritized for *actual* human adjudication; all untrusted differences and abstentions counted; even agreement between two uploaded drafts is NOT a human attestation.
- Stage99: fail-closed product release/readiness veto, independent of any self-asserted `approved` fields. 0 human-authenticated semantic labels as of writing.

## Stages100–103: a deliberately restricted original opacity diagnostic
`public-wholeframe-opacity-p0.mjs` takes original SHA-pinned RGBA and creates an SVG of **only pixels whose ORIGINAL alpha is exactly 255**. It chooses a byte-smaller of source-exact horizontal vs vertical rectangle covers. Every selected source mask pixel is exhaustively raster rechecked. All nonopaque pixels (alpha 0 or 1–254) stay excluded, and **opaque background is included**.
- Stage100: source exact alpha255 eligibility mask. Absolutely NOT a person's mask or silhouette; no generative infill.
- Stage101: exact rectangular vector decomposition and actual byte/vertex-cost statistics.
- Stage102: source-alpha diagnostic compared against original bitmap; alpha fringe and background semantics remain outside any claim of character preservation.
- Stage103: source-only gate stays HOLD, whole-character SVG budget **not inferred from this opacity mask**.

## Stage104: actual Chrome replay of SHA-pinned original opacity
Private replay used true GC001/Raden original 340x340 RGBA from prior private archive. Source opacity SVG at 340 and 680 in actual desktop Chrome, four renders **4/4 PASS**: 0 missing alpha255 pixels, 0 unexpected opaque pixels, 0 fractional alpha. Each case: source alpha255 pixels 115,152, other alpha 448; rectangle vertices 100, SVG bytes 507. **WARNING:** original opaque background is INCLUDED; this is NOT an independently segmented body silhouette or full-character budget validation. Diagnostic color is black, not source image color.

## Stage105: regression / research isolation / Golden veto
New `tests/js/test_public_stage96_105_p0.mjs` Node tests and Stage1–105 workflow registration. Previous baseline was 475 PASS at Stage95; the new actual CI verdict must be captured from runner logs after push.
Private original-derived SVG and SHA/chrome JSON remain in Drive ONLY. The Stage8 full-body polygon caps remain GC001 **3604>1887** and Raden **2370>1412** FAIL. No authenticated human reviewer labels, no person-vs-background human Golden, no whole-body SVG geometry budget pass, real iPhone Safari/HTTPS or rollback test. No release authorized. Next Stage106+ needs real human annotations and independent source-bound verification, not generated anatomy.
