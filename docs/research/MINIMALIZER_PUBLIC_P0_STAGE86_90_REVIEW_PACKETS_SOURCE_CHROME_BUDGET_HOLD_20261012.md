# MinimalizerPublic P0 Stages86–90: fullframe manual review packets and source-only verification (Golden HOLD)

2026-10-12. Research branch `research/public-structural-recovery-p0-part-preservation-20261011`, Draft PR #390. Scope strictly **MinimalizerPublic P0 private research**. No production route, Stage51 comparison UI, main or Local Minimalizer change. No AI inferred semantics, no pixels invented, no human Golden certification.

## Stage86: Reconcile incomplete Stage82–85 and fail-closed regression

- Recovered the previously untracked isolated `public-fullframe-review-packet-p0.mjs` and test scaffold rather than discarding existing work. This source-only code creates a packet from independently supplied original RGBA, face/background/historical masks and independent SHA digest verification. It rejects forged authenticated reviewer fields, changed bytes/metadata and suspicious review flags.
- `public-human-review-queue-p0.mjs`, `public-manual-draft-inspection-p0.mjs`, `public-manual-review-compare-p0.mjs`, `public-original-frame-proof-p0.mjs` from the previous attempt were read from latest PR head and covered by a new regression suite.
- Added **19 Node tests** across the recovered packet and existing Stage82–85 modules. These cover cross-source SHA, forged reviewer approval, disallowed alpha, self-certifying duplicates, case-specific mismatch, disagreement accounting, 1x/2x pixel proof and release veto. Previously existing run count was 442; new suite count expected 461, to be independently confirmed in actual GitHub Actions logs on the executable commit.

## Stage87: actual GC001/Raden original SHA review packets

Ran private original-source packet builder on both retained 340×340 original RGBA files, not generated/retouched images. **115,600 original pixels, 121 review tiles each**. Both complete source/eligibility-pinned packet SHA digests were recomputed from trusted original bytes. Two draft JSON templates contain only unreviewed label RLE of 115,600 pixels, the canonical original SHA identifiers, and approved=false. These are actionable input formats for manual review; **no real person annotated any pixel yet**. Packet records and replay script private Drive only.

## Stage88: isolated real Chrome original-frame proof

Actual Google Chrome canvas drew original SHA-verified RGBA at 340 and 680 px (GC001 and Raden, four render checks). **Opaque RGB mismatches 0, alpha mismatches 0** for both sources at both scales. Original nonopaque pixels: 448 at 340; 1,792 at 680. RGB under nonopaque pixels was **not** judged exact because compositing can premultiply/alter invisible RGB; this is not full 4-channel byte equality and not physical iPhone Safari/HTTPS proof. Source RGBA was never edited; the result does not establish background, skin, arms, sleeves, neckwear or hair semantic truth.

## Stage89: truthful whole-scene budget gate

Historical Stage8 full-body polygon budget baseline: GC001 3,604 vertices versus 1,887 cap (**1,717 over**), Raden 2,370 versus 1,412 (**958 over**). From independently retained Stage80 real-source-only fragments, four original-owner candidate snippets cost GC001 **7,982** (left+right) and Raden **20,060** selected contour vertices. These are **not the same output geometry or a full-body budget audit**. This method would not meet the historical full scene limits without substantial geometric changes. No new complete-scene candidate was constructed or approved. `PRIVATE_STAGE89_VERTEX_BUDGET_HOLD.json` records the failed gates.

## Stage90: verify, preserve, continue

GitHub executable/test verification must be recorded from actual CI after push. Private original evidence, Stage87 packet JSON, Stage88 Chrome replay and Stage89 gate stay in the existing canonical Drive project structure. Source-free JS/tests/docs only in GitHub. Keep PR Draft/HOLD and do not merge/deploy.

Outstanding: real **independently authenticated human semantic annotation** of full GC001/Raden image (including subject vs background, arms/hands, sleeves/skin, fine hair, necktie and entire silhouette), two independent label adjudications, whole-character opt-in SVG, original-source shape budget, Golden visual review, HTTPS physical iPhone Safari and tested rollback. No source-pixel overlap or semantic truth is automatically inferred from historical owner labels.

Next Stage91+ must prioritize completing independent human wholeframe segmentation and adjudication BEFORE any product-activation gate, then evaluate a new explicitly bounded full-character SVG without inventing pixels. Preserve SHA-pinned originals in Drive, not the public repo.
