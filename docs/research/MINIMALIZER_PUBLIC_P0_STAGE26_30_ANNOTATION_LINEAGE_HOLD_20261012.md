# MinimalizerPublic StructuralRecovery P0: Stage26–30 review data lineage (DRAFT / HOLD)

Date: 2026-10-12 JST. Repository `watarionn/Minimalizer`, research PR #390. All new code is isolated **Public-research-only**; no normal production route or Local Worker changes. Original photographs, RGBA buffers, historical arm/face masks, background observation and the private HTML with embedded photographs remain exclusively in private Google Drive, **never in GitHub**.

## Stage26: strict source-anchored draft ingestion

New `web/static/public-annotation-ingest-p0.mjs` consumes only Stage25's exact unverified draft schema. It demands two case-specific historical owner masks and independently provided source RGBA, face, background, SHA pins; validates every mask SHA, case name, dimensions, fixed labels, all RLE run lengths and code values (0..4), forbids assignments on face/background/transparent pixels and outside historical arms. Original PNG SHA is checked during private image preparation, while this module checks the supplied trusted PNG pin against the draft. Input `approved`, `productPromotionAuthorized` or alternate `reviewStatus` is explicitly rejected. A passing JSON is **syntax/byte-boundary valid, not anatomically correct**. It returns no product authorization and no source or mask bytes in audit JSON.

## Stage27: read-only topology

`public-annotation-topology-p0.mjs`: reports 4-connected components, tiny islands, adjacent label transitions and source RGB contrast boundaries. It **never** infers anatomy, and does not issue paint authorization. No original photograph or raw mask is exported in public report.

## Stage28: dual-review comparison, no trust promotion

`public-independent-review-compare-p0.mjs`: counts shared labeled pixels, disagreements, unknown/abstaining pixels and agreement by class. Inputs may be copied or forged; independent reviewer identities are *not verified*. Even 100% agreement cannot self-sign semantics. No painting until separately verified reviewer identity and human Golden.

## Stage29: private browser draft reimport

The enhanced offline review HTML is private only. The import feature refuses wrong case, mismatched lineage, unsigned/claiming-approval JSON, malformed RLE and edits to excluded pixels. Re-import preserves undo and shows the unverified status. Isolated system Chromium `about:blank` `set_content` test used an **explicit Python SHA-256 delegate**, because native secure-origin WebCrypto is absent in this environment and navigation to a mocked secure origin was blocked. Both GC001/Raden synthetic 49-eligible-pixel drafts imported, undo returned zero, a forged PNG SHA was rejected and resident labels remained unchanged. These 49 pixels are **synthetic parser tests, not human segmentation**. Normal HTTPS WebCrypto and iPhone Safari **NOT TESTED**.

## Stage30: regression gates

New `tests/js/test_public_annotation_ingest_p0.mjs`: 24 Node tests initially PASS locally. GitHub Actions run #38150691958 completed SUCCESS on research branch commit e328193e22e575235392ee853b7c1af02ba3bfee: 136 tests PASS / 0 FAIL across Stages 1–30 Node research suites. This does not certify full-image Golden, real HTTPS WebCrypto, reviewer identity, or production. All source-visible API exports return `productPromotionAuthorized:false`. Research remains Draft/HOLD. The previous GitHub Actions baseline was 112/112 tests PASS on Stage25 branch.

## Real case source-byte replay (private)

| Case | Verified historical visible arm pixels | Synthetic parser labels | Remain unclassified | Product authorization |
|---|---:|---:|---:|---|
| GC001 | 9,160 | 49 | 9,111 | NO |
| Raden | 20,177 | 49 | 20,128 | NO |

This did **not** fix the visual silhouette, skin/sleeve/hair boundaries, collar or held-object errors. Stage8 total whole-character vertices GC001 3604>1887, Raden 2370>1412 remain HOLD. Full-character PNG/SVG Golden and iPhone must be independently verified. The next meaningful quality step is a *trusted, human reviewed semantic classification* of historical arm, sleeve, hair and skin pixels (plus non-arm clothing), then a two-case side-by-side whole-character comparison without source-invented content. Prefer abstention over invented geometry, including for 6,249 historically unclassified color-mass pixels in Stage21.
