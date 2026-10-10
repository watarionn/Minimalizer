# MinimalizerPublic R22–R24 | Genuine frozen Stage8 source SVG serialization and held release gate

2026-10-10 | **R22 genuine source Chrome PASS; R23 genuine full SVG+gzip measurement PASS; R24 pre-release safety gate PASS as a verifier, PRODUCT NO-GO.**

## Canonical lineage / safety

This branch stacks on R19 Draft PR #376 and the held Public research lineage. It introduces **only** a read-only research verifier `scripts/verify_public_r22_r24_real_source_gate.py`, tests `tests/test_public_r22_r24_real_source_gate.py`, and this report. No `web/static`, Local Worker, source photographs, original Stage8 polygons, signed masks, published vendor assets, active hosting, main merge, or face-hidden specification were modified.

The R19 Stage8 input identity was doubly authenticated using frozen private source-scene JSON SHA and signed original-photo SHA. R22 additionally verified the original R19 research reports, including 11 owners, exact per-owner 340/680 Chrome comparisons and the saved PRIVATE SVG SHA. R22 independently reconstructed the 11-owner composite and compared it a second time in genuine Windows Chrome 154.0.8037.98 at 340px and 680px, with 0 different pixels at both sizes for GC001 and Raden.

**Important boundaries:** This is original **Stage8 11-owner composited SVG relative to the same frozen Stage8 source**, not direct pixel parity of Stage8 versus the protected original photo or full signed Stage04 image. Neither original-photo semantic arms/tie/staff/face correctness nor full-scene cross-engine resvg Facet parity is proven by it.

## R22 measured genuine browser evidence

| Case | Chrome native 340 changed pixels | Chrome 680 changed pixels | Stage8 original ring vertices | Historical hard cap | Historical budget |
|---|---:|---:|---:|---:|---|
| GC001 | **0** | **0** | 3,604 | 1,887 | **HOLD (+1,717)** |
| Raden | **0** | **0** | 2,370 | 1,412 | **HOLD (+958)** |

Both R19 research source variants selected `axis-relative` for all 11 owner masks. Real Windows run succeeded and the old R19 Windows `pytest` tests ran **7 PASS**, resolving R19's previously missing genuine source proof.

## R23 real 11-owner composite data, not only path strings

The verifier reconstructed both full composited source Stage8 SVG versions from the same 11 immutable owner polygons. It measured **complete UTF-8 SVG bytes**, deterministic `gzip.compress(level=9, mtime=0)` byte size and SHA-256, and actual Chrome canvas SVG decode+draw timing (7 samples for each representation and DPR). No claim that shorter SVG results in faster rendering.

| Case | Original full 11-owner SVG | Reencoded full 11-owner SVG | Full SVG saved | Original gzip9 | Reencoded gzip9 | Gzip saved |
|---|---:|---:|---:|---:|---:|---:|
| GC001 | 60,406 B | **27,539 B** | **54.410%** | 11,770 B | **4,798 B** | **59.235%** |
| Raden | 37,222 B | **14,685 B** | **60.548%** | 7,756 B | **2,810 B** | **63.770%** |

R23 genuine Chrome decode+draw timing is noisy. In the first seven-sample run, GC001 medians literal/relative: 340px **6.9/6.9ms**, 680px **30.4/32.5ms**; Raden 340px **6.8/7.0ms**, 680px **30.8/29.1ms**. A second independent run yielded different timing distributions but exactly the same bytes, compressed bytes, rendering equality and safety gate. Hence **no speedup or performance-regression certification**.

This is size optimization without changing any of the Stage8's 3,604 / 2,370 original vertices. It does NOT satisfy the historical cap. It is not a product algorithm performance improvement on photographs.

## R24 fail-closed integration research

The R24 read-only release gate requires:

- Both real signed frozen source cases with 11 owners, matching R19 report SHA and dual-DPR exact R22 browser evidence.
- Deterministically smaller whole SVG and gzip measurement available for R23, with no asserted speed signoff.
- Original R6 release matrix **8 blocked out of 15** gates, `releaseAuthorized=false`.
- Authentic R11 live host read-only evidence of CSS cache max-age=604800 seconds (7 days).
- Historical Stage8 original ring budgets, original image semantics, human Golden, whole-scene DPR2 Chrome/resvg Facet, real iPhone Safari, MPL legal redistribution and actual live rollback **all held**, not silently approved.

R24 result: `SOURCE_SVG_SERIALIZATION_RESEARCH_PASS_PRODUCTION_NO_GO`. Explicit `productionReleaseAuthorized=false`, `gitMainMerged=false`, `localMinimalizerModified=false`.

## Tests, repeatability, private data and follow-up

- Full Public R1–R24 selected regression and Local/Public isolation test suite: **144 pytest PASS**. New tests reject fake original Stage8 cap/vertex changes, missing owner, nonzero Chrome differences, forged human or speed signoffs, R6/R11 tampering and pre-existing output.
- Two independent full Chrome replays: **pixel parity, frozen source and output artifact SHA-256, full SVG/gzip compressed file metrics, gate exactly reproducible**; timing numbers intentionally not treated as deterministic. Canonical first metrics JSON SHA: `1d8c9f3531149f5e633d6db44071c3a491a1e552524dd373a719afa1c8bbbc83`.
- Source-derived SVGs and individual Chrome audit logs saved only to private Google Drive under `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R22_R24_20261010/`. GitHub holds script/tests/coordinate-free metrics report. No generated images.

Next safe task R25: establish **source-photo-grounded** owner/arm/tie/staff fidelity diagnostics and evaluate Stage8 vertex representation alternatives; keep old 1,887/1,412 caps unchanged. Even with lossless serialized SVG, no production deployment until all original R6 quality/legal/device/rollback gates are genuinely resolved.
