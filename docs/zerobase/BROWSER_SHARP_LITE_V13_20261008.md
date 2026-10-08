# BrowserFallback Sharp Lite v13

Date: 2026-10-08

## Goal

Improve geometrical clarity of BrowserFallback without introducing the color drift observed in `spectral-exact` on the Kyoko 340x340 source. Eyes/nose/mouth removal is intentional and not a defect. This is a **non-local** browser feature, unrelated to Local Worker production improvements.

## Previously verified ablation

Source: GC001 Kyoko 340x340, visually matched to the user-provided source (byte-identical match not established).

| Profile | Structural preprocessing | Contour | Main green color pixels | Sleeve RGB (95,275) | Rendered vertices |
| --- | --- | --- | ---: | --- | ---: |
| Lite | l0-lite-jacobi | independent rings | 1,873 | (65,66,74) | 1,409 |
| Lite + shared (candidate) | l0-lite-jacobi | canonical shared chain | 1,994 | (65,66,74) | 1,727 |
| Exact | spectral-exact | canonical shared chain | 4,111 | (32,42,80) | 1,571 |
| Geo with Lite preprocessing | l0-lite-jacobi | weighted Visvalingam shared chain | 2,018 | (65,66,74) | 2,853 |

The green count covers all pixels of the dominant green palette RGB, **not an isolated tie polygon**. Exact changes segmentation / grouping / palette when structural preprocessing changes, not from contour alone. See the independent [five-mode evidence](https://drive.google.com/drive/folders/1LwSrpUcGJ7Bdgwi2LmiAWqHurxLchlmq).

## Implementation

A dedicated `?browserFallback=force&browserFallbackQuality=sharp` opt-in selects:
- **Structural preprocessing:** `l0-lite-jacobi` (same as default Lite).
- **Region hierarchy / palette:** unchanged from Lite.
- **Contour:** existing `canonical-shared-chain` with OpenCV-compatible DP simplifier.
- **Raster:** existing `opencv-fillpoly-2x`.
- **Code footprint:** no external runtime package or model download.

`?browserFallbackQuality=lite` and `?browserFallbackQuality=exact` retain their existing implementations. Sharp persists in the same existing localStorage quality setting until reset. The output response exposes `X-Minimalizer-Browser-Quality-Profile` and a `qualityProfile` metadata field, and the UI identifies `SHARP LITE (experimental)`.

**Fail closed:** if Sharp Lite is requested but either the shared contour module or OpenCV-compatible raster module is unavailable, the engine raises an error rather than silently reverting to fuzzy Lite rings.

## Acceptance gate

1. Focused tests: same source/preprocessor must yield identical palette centers, per-shape owner/color assignment, shape budget and background in Lite vs Sharp. Output geometry alone can change. Determinism and contour IoU/topology guards must hold.
2. Existing BrowserFallback v12 tests and JavaScript syntax gate.
3. Real Chrome 340x340 Kyoko three-way Lite / Sharp / Exact comparison, **including the actual UI query parameter path**. Record PNG, area/color metrics, vertices, contour/raster method, processing time and output hashes.
4. On a second representative source, inspect for regressions. A positive Kyoko alone is insufficient for promoting defaults.
5. Save images, measurements and test harness to the existing Google Drive `chatGPT及びCodex用/Minimalizer` hierarchy, research and code to GitHub.
6. Only after verified quality and regression gating determine merge / deploy. Default stays unchanged; no production claim before release validation.

Status: **IMPLEMENTED IN ISOLATED BRANCH; PRODUCTION DEFAULT UNCHANGED; REAL CHROME VALIDATION PENDING.**
