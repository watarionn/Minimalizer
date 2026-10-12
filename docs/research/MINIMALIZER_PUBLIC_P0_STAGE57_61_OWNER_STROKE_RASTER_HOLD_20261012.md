# MinimalizerPublic P0, Stage57–61: real historic-owner SVG stroke audit

Date: 2026-10-12. Research-only Draft PR #390, no modification of main, normal production Public, Stage51 public preview, or Local Minimalizer. No generative completion, new source colors, fake skin/sleeve/hair semantics, facial details or default converter change.

## Stage57: source-exact local axis sweep

`public-source-tiled-stroke-p0.mjs` independently pins each source-observed mask SHA256, partitions it into disjoint 8/16/32/64/128 tiles, selects the most compact exact horizontal/vertical run-based butt-stroke encoding in each tile, and **falls back to the previous global-axis encoding** unless the tiled version is strictly fewer stroke segments. Never drops source pixels, and does not authorize any painting. Pixel membership is independently checked at 340/680 by Stage59. This is not a copy of the original bitmap encoded in SVG.

## Stage58: pinned historic owner observations, not independent anatomy

`public-source-owner-stroke-audit-p0.mjs` reuses Stage31's SHA-256-pinned full-source RGBA, historic signed left/right owner masks, face mask and *unsigned background observation* to calculate eligible pixels, conservatively excluding face, background and alpha. Historical `left_arm`/`right_arm` are **old pipeline owner identifiers, not independently authenticated arm/skin/sleeve labels**. No RGB painting, no reconstruction or semantic promotion. Source data and bitmap files remain private in Drive.

## Stage59: mathematical and real Chromium 1x/2x proof

`public-source-stroke-raster-audit-p0.mjs` independently checks disjoint rectangles with exact 1x/2x pixel coverage, rejecting overlap, spill, lost pixels and malformed strokes. Real isolated Chromium then rendered original signed-source eligible masks as SVG strokes via canvas at 340×340 and 680×680, reading RGBA. **Eight of eight case/owner/resolution tests: 0 mismatched pixels, 0 spill, 0 lost, 0 partial alpha.** This verifies only the historical mask geometry's lossless encoding. It does not validate actual person anatomy, color or product SVG rendering.

## Stage60: real-case results, true value gate

`public-source-stroke-value-gate-p0.mjs` rebuilds candidates independently, verifies exact SVG string and stroke arrays, refuses manipulated input and reports segment/byte costs without conflating endpoints with Stage8 polygon vertices.

| Case / old owner label | Eligible source pixels | Global strokes | Best tiled strokes (tile 64) | Selected strokes | SVG paths markup bytes |
|---|---:|---:|---:|---:|---:|
| GC001 / left_arm | 2,715 | 104 | 113 | 104 global | 4,327 |
| GC001 / right_arm | 6,445 | 109 | 120 | 109 global | 6,522 |
| Raden / left_arm | 10,307 | 131 | 165 | 131 global | 8,367 |
| Raden / right_arm | 9,870 | 95 | 100 | 95 global | 5,732 |

GC001 historic source eligible total **9,160**; excluded background observation 41. Raden total **20,177**; excluded background 112. Face/alpha exclusions observed 0 within these raw masks. The tile sweep 16/32/64 **never improved the existing global-axis segment count**, so the tiled alternative is rejected for all four cases. This is useful negative experimental evidence, not a claimed new complexity breakthrough. Segment endpoints cannot be substituted into the Stage8 full-body vertex budget.

All source PNG, source masks, signed pixel geometry, source RGBA, Chrome captures and per-pixel comparisons are **PRIVATE**, stored only under the canonical Drive folder. Code, synthetic unit tests and aggregate measurements are safe for GitHub.

## Stage61: CI and release veto

New **31 Node unit tests** cover SHA and eligibility, exact source mask accounting at 1x/2x, fallback selection, tamper rejection and immutable source provenance. They are added to the existing research test entrypoint, not to the Public conversion route. GitHub Actions cumulative expected 334 tests; the exact CI run, result and commit are recorded separately after execution.

No independently verified sleeve/skin/hair pixels (0). Historical full-character SVG Stage8 vertex limits still fail GC001 3,604>1,887 and Raden 2,370>1,412. No human Golden 340/680, no true native iPhone Safari, no full body color fidelity pass, no approved production release. **PR #390 Draft/HOLD**. The next step should focus on obtaining provenance-backed human anatomy boundary evidence and a *visually meaningful, source-contained full-body rendering candidate*, not expanding label bookkeeping indefinitely.
