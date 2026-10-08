# BrowserFallback Facet v15: bounded shared-arc straightening

Date: 2026-10-08
Scope: **BrowserFallback only**, non-local; do not alter Local Worker, ZeroBase2, or image generation policies.
Repository: `watarionn/Minimalizer`
Branch: `feat/browser-facet-v15-guarded-refinement-20261008`
Development PR: [#227](https://github.com/watarionn/Minimalizer/pull/227)
Status: **REAL-CHROME QUALITY GATE PASSED / integration-release gate separate**.

## User requirement

The target is intentionally minimal geometric color fields, not re-creation of eyes, nose or mouth. BrowserFallback's persistent weakness is jagged, wandering borders between flat color areas. Exact's spectral structural preprocessing enlarged Kyoko's green necktie and recolored the left sleeve. Preserve **Lite preprocessing and palette**, while making the existing Shape v14 shared contours read as fewer, cleaner geometric segments.

## Existing architecture / unchanged paths

- `lite`: default `l0-lite-jacobi`, independent rings + Canvas.
- `sharp`: `l0-lite-jacobi`, shared-arc contour + OpenCV-compatible 2x raster.
- `shape`: same Lite structure and palette, plus conservative corner-aware simplification.
- `exact`: existing opt-in `spectral-exact` (unchanged).
- New experimental `facet`: **same Lite preprocess, ownership, palette and Shape v14** plus one more conservatively guarded shared-arc straightening pass.

The mode is selected only through `?browserFallback=force&browserFallbackQuality=facet` once deployed. Defaults and earlier mode routing stay unchanged. No hosted API, new JavaScript dependency, GPU, image generation or independent color segmentation.

## Implementation

Files: `web/static/canonical-contour.js`, `web/static/browser-fallback.js`, `web/static/app.js`.

Unlike v14's whole-chain simplification proposal, `facet-safe` evaluates individual removable inner vertices on each shared boundary chain. A candidate replaces two adjacent segments by one straight chord. It adds no new vertex or image content; **both regions still share the same arc** and its endpoints are fixed.

1. Map current contour points back to the full original raw boundary.
2. Do not consider a proposed vertex removal if *any* raw boundary point crossed by the chord is farther than **2.35 px** from the chord.
3. Prefer candidate chords whose directions are near multiples of 45°, without moving endpoints or forcing exact angles. Other small safe steps may still be simplified.
4. Preserve strong corners of at least **55°** when sufficiently supported on both sides by straight segment runs totaling at least **3.5 px**. Guard considers accumulated collinear support, rather than just the immediately adjacent segment.
5. Each candidate must pass the existing no-self-crossing, region connectivity/holes, 0.90 min IoU, area, centroid and directional extent checks, and must not reduce the affected region's IoU by more than **0.0025 relative to the chain-local Shape baseline**.
6. Bound work: at most **14 evaluations and 5 accepted removals per shared arc**, with deterministic candidate order and explicit accepted/rejected counters. Missing contour/raster modules or incompatible structural mode fails closed.
7. Export `facetRemovedVertices`, `facetRefinedChains`, `facetTrialCount`, `facetRejectedCandidates`, `contourGeometryMode`, and `X-Minimalizer-Contour-Facet-Removed-Vertices`.

Important: the 0.0025 figure is **per processed chain's fixed pre-Facet region baseline**, not a promise of a 0.0025 global worst-region drop across all chains. The existing global minimum-IoU hard gate remains active.

## Correction during verification (retained regression)

An initial synthetic corner test found a real flaw: a large 90° corner subdivided into multiple short consecutive collinear edges could be misidentified as a small notch because immediate-neighbor arms were each only 2 px. The algorithm was corrected to measure contiguous straight **support runs** extending beyond the immediate neighbors and protect the substantial corner. This is a real logic fix, not a weakened test. The correction was followed by full Chrome re-benchmarking of all 3 sources and all 5 profiles. The corrected outputs happened to be byte-identical to the initial candidate on these 3 real samples.

## Real-Chrome final benchmark

Chrome 154, self-hosted static site, actual `app.js requestBrowserFallback()` route, original 340×340 Kyoko/Noel/Ririka source PNGs, subject guidance `browser-u2netp`. All profiles share maximum 40 shapes, palette target 8, equivalent SLIC and analysis/work size settings. Five independent PNGs generated per image.

| Character | Shape v14 vertices | Facet v15 vertices | reduction | Facet min region IoU | Changed pixels vs Shape | 4-neighbor color transitions delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyoko | 1,513 | **1,377** | **9.0%** | 0.90206 | 0.0848% | -12 |
| Shirogane Noel | 1,366 | **1,232** | **9.8%** | 0.90294 | 0.2318% | -51 |
| Ichijou Ririka | 976 | **880** | **9.8%** | 0.90074 | 0.1237% | -13 |

Profile `facet` processing times in the guarded final rerun were approximately 4.91s / 4.37s / 4.32s for Kyoko / Noel / Ririka, similar order to Sharp/Shape and well below Exact. These are Chrome wall timings from single runs, not a statistically robust performance distribution.

- All 3 previous `lite`, `sharp`, `shape`, `exact` mode PNGs match the archived v14 results **byte-for-byte by SHA256**.
- The live UI path and direct Facet engine invocation produce **byte-for-byte identical PNGs** on all 3 samples.
- Kyoko representative green color RGB(149,211,27) is **1,994 pixels** in Sharp, Shape, and Facet. This count refers to the whole image's dominant green palette color, not to an individually annotated necktie shape. Exact's dominant green occupies 4,111 pixels.
- Kyoko sampled sleeve RGB at (95,275) remains **(65,66,74)** in Lite, Sharp, Shape and Facet; Exact uses (32,42,80).
- Per-region ownership and palette center/assignments are unchanged by construction; controlled Node tests verify parity and deterministic outputs.

### Visual review

Six-column comparison sheets include source, Lite, Sharp, Shape, Facet, Exact for each sample. Facet's changes are subtle: short staircase segments decrease and major character/color masses remain. **Some visible stair-stepping persists**, so this is another measured incremental geometric improvement rather than final ideal graphic abstraction. Do not substitute vertex reduction alone for artistic review.

## Reproducibility, automated tests and evidence

- `tests/test_browser_facet_v15.py`: mode contract; endpoint-corridor angular candidate; aggregated straight-run protection of meaningful right angles; palette/ownership identity; deterministic replay; topology/IoU; missing modules and incompatible route fail closed.
- Existing `tests/test_browser_shape_v14.py` and `tests/test_browser_sharp_lite_v13.py` were updated **only** to allow the additional explicit `facet` quality profile; their original safety invariants remain.
- Isolated Windows checkout focused and v12 graduation suite: **47 passed**; JS syntax and Python replay-script compile PASS.
- GitHub PR Actions: **Browser Facet v15, Browser Shape v14, Browser Sharp Lite v13: all PASS**.
- Replay: `tools/run_browser_facet_v15_chrome_compare.py` on the same browser source, with no Local Worker.
- Image/metrics sources of truth: [Google Drive / chatGPT及びCodex用 / Minimalizer / BrowserFallback_GeometryV13_20261008 / ShapeV14_20261008 / FacetV15_20261008](https://drive.google.com/drive/folders/1LkGY8T-yayAjHIzRSi3CHbdcT4MPY5mI): 3-source six-mode comparison, upper/torso closeups, JSON metrics, written review, compressed independent inputs/outputs and replay scripts.

## Release boundary

This is an explicit `facet` experimental quality profile, **not** an automatic replacement for existing Lite/Sharp/Shape/Exact. A production release must explicitly verify merge, static Shin deployment without touching unrelated files, remote public-JS byte hashes, actual live Chrome output against the accepted per-source SHA256, and persistent rollback copies. Until those checks pass, do not describe this as deployed.
