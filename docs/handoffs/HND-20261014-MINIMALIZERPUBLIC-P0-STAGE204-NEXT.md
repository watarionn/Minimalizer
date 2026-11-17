# Handoff: MinimalizerPublic StructuralRecovery P0 after Stage204

Date: 2026-10-14 JST
PR #393: https://github.com/watarionn/Minimalizer/pull/393
Status: Draft / Golden HOLD / unmerged; main, live Public, Local unchanged.

## Stage204 finished
- Implemented exact observed pixel-grid contours, hole-safe and diagonal-touch-safe, with fail-closed scanline raster proof, zero subject spills/loss.
- Added 10 source-free tests and updated research CI. Actual Actions run https://github.com/watarionn/Minimalizer/actions/runs/38534856200 at `7b20453e`: **678 tests PASS, 0 fail**.
- Real PRIVATE source: GC001 6,292 -> 4,588 vertices (-27.08%); Raden 3,532 -> 2,436 (-31.03%) versus Stage203 exact rectangle encoding. Actual local Chromium renderer replay **0 pixel mismatch** both cases.
- The mask is just two-reviewer *agreement proposal* with disputed areas excluded. Wholebody Golden and numeric cap both FAIL: GC001 4,588>1,887; Raden 2,436>1,412.
- Source-free module `web/static/public-stage204-source-exact-contour-p0.mjs`, unit tests `tests/js/test_public_stage204_p0.mjs`, evidence narrative `docs/research/MINIMALIZER_PUBLIC_P0_STAGE204_SOURCE_EXACT_CONTOUR_GOLDEN_HOLD_20261014.md`.
- Source-derived private ZIP only in owner-only `chatGPT及びCodex用 / MinimalizerPublic / StructuralRecovery_P0_20261010 / Stage204_Private_SourceExactContour_20261014`; do not commit private files.

## Stage205 starting point
1. Review original art and Stage193 PRIVATE adjudication packet. Class definitions: sleeve vs garment (Raden), accessory vs garment (GC001), then hair/skin/background boundary.
2. Human operator explicitly adjudicates uncertain pixels, preserving A/B v1 originals; produce SHA-pinned v2 corrected reviews only when manually confirmed.
3. Separate class-label agreement from certified semantic ground truth. No generator, no inventions, no automatic majority/role relabeling; do not silently fill withheld opaque pixels.
4. Evaluate additional source-pixel-exact contour/region frontier while preserving zero spill & actual renderer replay, then full character shape, geometry caps, internal colors, realistic browser QA, physical iPhone and rollback.
5. Keep PR Draft until independent Golden + full-body vertex/RGB/shape gates + rollback and explicit operator release approval all pass.

**Stop gate unchanged: HOLD, zero product release authority.**
