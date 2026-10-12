# MinimalizerPublic StructuralRecovery P0 Stage72–76: signed review transport, exact color fill, real Chrome (Golden HOLD)

2026-10-12; `watarionn/Minimalizer`, Draft PR #390; branch `research/public-structural-recovery-p0-part-preservation-20261011`. Source authority GC001/Raden original 340×340 RGBA and SHA-256 masks from the established Stage67–71 PRIVATE Drive archive. Only opt-in research files in the PR; main/Local Minimalizer/normal Public/Stage51 deployed preview are untouched. **No generated pixels, semantic owner invention, automatic paint, or release approval.**

## Stage72: independently pinned receipt transport, NOT independent human authority

`public-review-attestation-boundary-p0.mjs` accepts an untrusted Stage25 draft only after independent Stage26 SHA/eligibility verification, independently recomputes Stage31 source-eligible mask and SHA, and can validate a P-256 ECDSA receipt binding source RGBA SHA, original PNG SHA, labels SHA, eligible mask SHA, case ID, and an **out-of-band pinned** reviewer public key. It rejects forged signatures, changed key pins, altered labels/source bytes, cross-case drafts and out-of-source pixels.

**Scope limitation:** a mathematically valid signature does not identify a human or certify label correctness. No independently authenticated reviewer/key-registration service or independently verified whole-character semantic segmentation was provided. Stage72 **does not claim completion of human review**, remains 0 independently attested anatomy pixels; signing tests use generated synthetic keys and are not human review.

## Stage73: exact fill-based candidate compared to Stage68 colored butt strokes

`public-source-exact-color-fill-p0.mjs` validates real independently SHA-pinned RGBA/owner/palette through existing Stage68 guards. For each original-source medoid-color pixel set, it generates exact disjoint integer-aligned rectangular fills, searching horizontal/vertical merging and choosing by serialized path bytes; refuses source pixel overlap or added/omitted pixels. No source bitmap is embedded in SVG. All original color medoids must occur in the owner source. It reports real `fillSvgBytes`, `stage68StrokeSvgBytes`, and honest `explicitRectangleVertices=4*rectangles`; stroke endpoints are not equated to vertices.

Real GC001/Raden historic owner candidates:

| Candidate (historical mask name, NOT anatomically certified) | Stage68 stroke SVG bytes | Stage73 fill SVG bytes | Saved bytes | Rectangle vertices |
|---|---:|---:|---:|---:|
| GC001 left_arm | 18,740 | 12,396 | 6,344 (33.9%) | 2,996 |
| GC001 right_arm | 29,946 | 23,528 | 6,418 (21.4%) | 6,136 |
| Raden left_arm | 56,548 | 52,469 | 4,079 (7.2%) | 12,968 |
| Raden right_arm | 40,042 | 36,661 | 3,381 (8.4%) | 9,672 |
| **SUM (isolated 4 source-only regions)** | **145,276** | **125,054** | **20,222 (13.9%)** | **31,772** |

The byte reduction is real for these four private SVG snippets only, NOT proof of full-character SVG simplicity, anatomy, semantic accuracy or acceptable full-scene silhouette. Stage8 old full-character polygon vertex limits GC001 3604>1887 and Raden 2370>1412 remain unresolved. These new rectangle vertices cannot be substituted to claim that earlier budget passed.

## Stage74: re-derivation and independent pixel-membership checks

From original source bytes independently supplied to the verification call, reconstruct the candidate SVG exactly and check byte identity, layer geometry, original source/owner hashes, 4-connected original membership, layer non-overlap and overall coverage. Tests deliberately forge path, rectangle geometry, cost verdict, palette membership, assignments and signed lineage; all fail closed. Verification emits `SOURCE_FILL_REPLAY_PASS_GOLDEN_HOLD` with `releaseAuthorized=false`.

## Stage75: *real original* 340/680 Chrome rendering

Private replay takes both original-source RGBA/masks/manifests from the earlier Stage67–71 private source ZIP, reruns Stage62/63/67 source medoids and Stage73/74, and renders each resulting SVG using actual Google Chrome on Windows. Source expected RGBA is built from **only original eligible pixels and actual original-observed palette colors**; 340px and 680px canvas buffers are compared byte/pixelwise. 4 historic regions × 2 scales = **8/8 PASS**: lost 0, extra 0, wrong RGB 0, fractional alpha 0. Generated SVGS, screenshots, and exact JSON metrics are PRIVATE only in Drive; GitHub includes no original/source bytes. This is **isolated Chrome, not a Public domain HTTPS or physical iPhone Safari test**. Chrome render with imageSmoothingDisabled is not an iPhone Safari Golden substitute.

## Stage76: local cross-stage verification, CI and HOLD

Research module/test+workflow registered. Source-only Node regression: **413 passed / 0 failed / 0 skipped locally**, including 27 new Stage72–76 tests (386 prior Stage71). Actual GitHub Actions run **38200219356**, job **114651745649** on executable/test SHA **8c5557ecf4baa0ea341e8e3f8829968af05475db**: decoded runner log **413 tests PASS / 0 failed / 0 skipped**. See `MINIMALIZER_PUBLIC_P0_STAGE76_CI_413_PASS_GOLDEN_HOLD_20261012.md`.

Hard blockers: **0 independently verified human skin/sleeve/hair pixels**, missing arms/neckwear/hair full-character Golden, whole-scene SVG budget, actual iPhone Safari, live secure Public origin, rollback. This source-only color transport does NOT authorize paint or deploy. **PR remains Draft HOLD, do not merge.**

## Provenance / preservation

- Public code: `web/static/public-review-attestation-boundary-p0.mjs`, `web/static/public-source-exact-color-fill-p0.mjs`; `tests/js/test_public_review_and_color_fill_stage72_76_p0.mjs`.
- Canonical private archive source input: Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage67_71_20261012/MinimalizerPublic_P0_Stage67_71_PRIVATE_20261012.zip`.
- Target new Drive archive: `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/PartPreservation_Stage72_76_20261012` for this report, handoff and PRIVATE generated SVG/Chrome evidence.
