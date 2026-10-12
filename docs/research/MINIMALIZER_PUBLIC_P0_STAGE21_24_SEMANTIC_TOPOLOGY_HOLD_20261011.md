# MinimalizerPublic P0 StructuralRecovery Stage21–24: source semantic review boundary

Date: 2026-10-11. **RESEARCH PASS for topology/read-only protections. VISUAL / SEMANTIC / PRODUCTION: HOLD.** This work never draws new source-absent pixels, and does not use image generation, img2img, or any Generative Fill.

## Motivation

Stage17–20 proved that even *historically signed arm masks* can include backdrop and long hair; they are not evidence that every pixel belongs to sleeve or skin. The Stage18 mass repaint produced RGB improvements (GC001 +3.93%, Raden +6.41%) but obvious material/anatomy corruption, rejected by human visual observation. An independently reviewed source-level ownership boundary must precede any further sleeve, forearm, hair, collar or prop repaint.

## Stage21: source-only connected-component audit

New research-only `web/static/public-semantic-review-packet-p0.mjs` verifies SHA-256 of 340x340 original decoded RGBA, historically signed left/right arm masks, signed face mask, external observed-background mask, and all Stage18 partition masks. It intersects owners with visible original source (no face/background/alpha), rejects missing/duplicate/spoofed source origins or painting beyond owners, and builds a **read-only** inventory. Each color partition is decomposed into 4-connected components; per-component bounding boxes, sizes, touched signed-owner boundaries, proximity to observed background and high-contrast source edges are counted. These are diagnostic signals only. In particular, a high contrast edge cannot itself identify hair vs sleeve, and SHA-256 does not sign the meaning of a segmentation mask.

Actual pinned GC001/Raden replay:

| Metric | GC001 | Raden |
|---|---:|---:|
| Source-observed Stage18 color partitions | 7 | 7 |
| Total 4-connected components in those partitions | 25 | 126 |
| Color partitions with >1 component | 5 | 7 |
| Unclassified historically owned but visible original pixels, left arm | 960 | 2,287 |
| Unclassified historically owned but visible original pixels, right arm | 1,309 | 1,693 |
| Contacts with observed background, counted as adjacent edges | 118 | 23 |
| Contacts with historical arm owner boundary, counted as edges | 666 | 724 |
| Contrast >=96 (sum RGB channel differences) along observed-mask boundaries, edge count | 1,403 | 1,609 |

All values derive from SHA-pinned real source masks with deterministic replays; they are *not* validated anatomical labels. 14 observed partition regions -> 151 connected components. There are **6,249** historically owned and visible source pixels not covered by the 14 proposed mass regions across the two cases. Never treat absence of a partition as background.

## Stage22: independent reviewer boundary

`web/static/public-semantic-review-admission-p0.mjs` allows hypothetical class annotations (`sleeve`, `forearm_skin`, `hair`, `garment`, `accessory`, `unknown`) only as **untrusted proposals**. SHA mismatches, duplicate annotations, invalid IDs are rejected. Even an annotation claiming `approved:true` or a copied hash is not independent human signoff. There is no trusted reviewer signature verifier in this research module, so it cannot issue approval or promotion.

## Stage23: fail-closed before any recolor

`gateSourceOwnerPaint` requires both real cases in the audit and always denies Stage18 repaint while independent sleeve/skin/hair owner masks and trusted reviewer attestation remain unavailable. Real two-case result: `DRAFT_HOLD`, 11 explicit blocker records, `stage18PaintAllowed:false`, `productPromotionAuthorized:false`. **The 11-blocker total uses a NEW source-review gate. It is not an improvement from the separate 13-blocker Stage19 global release gate.** The previous Stage18 rejected preview is retained exclusively as evidence, not adopted as a visual candidate.

## Stage24: verification / preservation

- 25 NEW Node `node:test` cases, including tampered source, historical owner masks, background, partition masks, untrusted annotation flags, disconnected components and forged approval receipts, pass in a repository-matching directory layout.
- PRIVATE diagnostic contact sheets show original source, frozen Facet40 and translucent **annotations** of untrusted regions. These are not edited product pictures and do not contain generated visual content. Original source images, historic masks, source color regions, raw RGBA and actual case packets MUST remain off public GitHub.
- Public report, isolated modules/tests and handoff live only on PR #390 research branch. The private archive and replay evidence live in Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage21_24_20261011`.

## Still required before product integration

Independent pixel-level reviewer-defined masks for each visible `sleeve`, `forearm_skin`, `hair`, `collar`, `accessory`, with trusted source lineage and exclusive overlaps; source-signed torso/held-prop boundaries and semantic z-order; genuine improvements in whole-character silhouettes without missing arms, face feature suppression including outside historical mask, full SVG vertex budget, real secure-origin browser WebCrypto, 340/680 full-character and iPhone Safari Golden, dependency licensing, rollback verification. NO CHANGE to `main`, live Public, or Local Minimalizer. PR stays **Draft/HOLD**.
