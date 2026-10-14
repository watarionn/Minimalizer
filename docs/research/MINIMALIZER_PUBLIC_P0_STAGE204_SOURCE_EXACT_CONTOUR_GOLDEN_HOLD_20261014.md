# MinimalizerPublic StructuralRecovery P0 | Stage 204 exact-source contour research

Date: 2026-10-14 JST. Existing PR #393 Draft, Golden HOLD. No production or Local Minimalizer changes.

## Implementation
Added `web/static/public-stage204-source-exact-contour-p0.mjs`, source-free ES module `buildExactObservedBoundary`.
- Accepts only 0/255 masks on bounded, case-scoped image sizes, not private originals in public repository.
- Traces four-sided boundaries with the subject on the right; at diagonally contacting vertices prefers right turns; keeps independently closed loops and internal holes.
- Removes consecutive collinear vertices ONLY, retaining integer source pixel-grid vertices; emits `evenodd` SVG paths.
- Rasterizes output internally and rejects any spilled or lost source pixel. It never synthesizes missing semantic pixels, uses color-only inference, or authorizes production.
- Test `tests/js/test_public_stage204_p0.mjs` includes 512 exhaustive 3×3 masks, seeded 16×16 fuzz patterns, hole/diagonal cases, pathological checkerboard, malformed input and no-Golden guards.

## Actual PRIVATE original-source verification (aggregated metrics only)
Source RGBA was SHA-checked in owner-private storage; original reviewer submissions A/B were matched to corresponding original-case hashes. Subject masks include **only** the fully opaque pixels for which A and B proposed the same nonbackground class. Their agreement is a *proposal*, NOT human-certified semantic ground truth. Original source, reviewer data and pixels were unchanged; all disputed/abstained pixels are withheld.

| Case | Source-proposed person pixels | Withheld opaque pixels | Previous exact rectangles / vertices | Stage204 exact contour loops / vertices | Vertex reduction | Historical fullbody cap |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| GC001 | 47,448 | 7,072 | 1,573 / 6,292 | 232 / 4,588 | 27.08% | 1,887 (FAIL) |
| Raden | 47,888 | 22,690 | 883 / 3,532 | 96 / 2,436 | 31.03% | 1,412 (FAIL) |

These vertex counts compare **different encodings of the same incomplete, agreed-person candidate mask**. The numeric budget remains above target; they are NOT complete wholebody vectors, not certified silhouettes and not Stage8 contour-equivalent figures.

Pixel-exact independent raster checks:
- Module-level evenodd scanline raster replay: source-only, zero spill, zero loss, both private cases.
- Independent local headless Chromium 340px SVG rendering vs separately decoded original masks: **0 pixel mismatches** both cases.
- No source originals, A/B labels, RGBA, private masks or SVG derivatives uploaded to public repository or public CI.

## Regression & evidence
- Source-free Stage204 unit test: 10/10 PASS on local Node + authorized PC.
- Whole PR research CI: **678/678 PASS**, fail 0, on head `7b20453e350da9530d5a2da48a99efd6aac0d218`; https://github.com/watarionn/Minimalizer/actions/runs/38534856200.
- Private original-derived SVG/mask/reference screenshots + auditable benchmark ZIP retained in owner-only Google Drive below `chatGPT及びCodex用 / MinimalizerPublic / StructuralRecovery_P0_20261010 / Stage204_Private_SourceExactContour_20261014`.

## HOLD and next
- A/B reviews remain independent per operator testimony; **pixel-level class disagreements are NOT adjudicated**, notably Raden sleeve/garment and GC001 accessory/garment.
- Both exact contours **exceed** historical geometry caps, and withheld pixels prevent fullbody certification.
- Physical iPhone Safari acceptance, final Golden visual quality, source-faithful complete interior colors and real rollback still unverified.
- Stage205: prioritize manual source-image class adjudication, immutable separate correction versions, and diagnostics for unresolved boundaries. Also explore alternative **source-exact** SVG representations and measured complexity improvements without invented pixels.
- Do not merge PR #393, deploy production, alter Local Minimalizer or claim release authorization.

**Gate: GOLDEN HOLD / Draft / no production paint authority.**
