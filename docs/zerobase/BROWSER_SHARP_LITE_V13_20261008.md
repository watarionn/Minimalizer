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

Status: **PRODUCTION VERIFIED / opt-in Sharp profile shipped; default Lite unchanged.**


## Actual browser benchmark: Chrome 154 / three 340x340 sources

Fully completed from isolated checkout at initial Sharp Lite candidate commit `082a114b`. The later workflow/benchmark/documentation commits do not modify image-generation logic.

| Source | Lite vertices | Sharp vertices | Exact vertices | Lite sec | Sharp sec | Exact sec | Sharp min region IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyoko GC001 | 1,409 | 1,727 | 1,571 | 3.84 | 3.74 | 11.40 | 0.9021 |
| Shirogane Noel | 1,555 | 1,576 | 2,009 | 3.63 | 5.79 | 14.18 | 0.9021 |
| Ichijou Ririka | 1,262 | 1,108 | 1,214 | 3.62 | 2.68 | 11.04 | 0.9037 |

All 3 sources: `shapeCount=40`, `subjectGuided=true`, `qualityProfile=sharp`, `structuralPreprocess=l0-lite-jacobi`, `contourMethod=canonical-shared-chain`, `rasterMethod=opencv-fillpoly-2x` in the Sharp path. Original `lite` and `exact` profiles still resolve to their historical structural/contour methods.

### User-reported Kyoko palette regressions: resolved in Sharp candidate

- Green palette mass, measured as dominant green RGB pixel count (not a manually segmented tie area): Lite **1,873**, Sharp **1,994** (+6.5%), Exact **4,111** (+119.5% vs Lite).
- Left sleeve at pixel (95,275): Lite **RGB(65,66,74)**, Sharp **RGB(65,66,74)**, Exact **RGB(32,42,80)**.
- Sharp vs Lite changed-pixel ratios: Kyoko **4.263%**, Noel **4.105%**, Ririka **3.363%**. Much of this reflects replacing independent antialiased Canvas rings with fixed-color shared polygons, rather than reassigning color region owners. It is not an SSIM improvement claim.
- Pixel-perfect regression checks: present Lite vs previous v13 control Lite: **identical**; present Exact vs previous v13 control Exact: **identical**; new Sharp vs previously benchmarked Lite+shared: **identical**.
- Controlled Node test confirms the same palette centers, shape ownership, chosen palette IDs, per-owner colors, background, and preprocessor for Lite and Sharp. The output polygon geometry is the intended changed dimension.

### Real application routing

The test page loaded `?browserFallback=force&browserFallbackQuality=sharp` and verified actual `app.js` configuration:
`{profile:sharp, structural:l0-lite-jacobi, canonical:true, forced:true}`.
Then it invoked the real `requestBrowserFallback()` (not only `engine.minimalizeFile()`). The response advertised quality=sharp, shared contour, OpenCV 2x raster, and produced a PNG **byte-for-byte identical** to direct Sharp execution.

### Automated tests

- GitHub Actions Sharp Lite workflow: **PASS** after fixing a workflow-only shallow-checkout diff check. JS syntax, focused tests and PR whitespace check passed.
- On isolated real checkout: **4 Sharp Lite focused tests PASS**.
- Extended regression: **40 PASS, 1 excluded**. The excluded case is a **pre-existing stale v5 spectral test** (`tests/test_browser_fallback_v5_spectral.py::test_browser_v5_exact_mode_reports_structural_profile`), already in `main`; it expects `browser-fallback-v11` although the current runtime and all v12 tests correctly report `browser-fallback-v12`. Its original unsuppressed run was 40 passed, 1 failed. Do not misreport the unsuppressed extended suite as passing; this unrelated stale-version assertion requires separate cleanup.

### Preserved evidence and replay

[Google Drive: chatGPT及びCodex用 / Minimalizer / BrowserFallback_GeometryV13_20261008 / SharpLiteV13_20261008](https://drive.google.com/drive/folders/1cH22ujGWJWORg1n9-Zpk3nHV0Cycp1Lw)

- `sharp_lite_three_source_4way.png` (source, Lite, Sharp, Exact for Kyoko, Noel, Ririka)
- `sharp_lite_kyoko_torso_2x.png`, `sharp_lite_kyoko_upper_2x.png`
- `sharp_lite_metrics.json`, `sharp_lite_report.md`
- `sharp_lite_v13_evidence_20261008.zip` (contains all 3 sources, 3 result PNGs/source and metadata per case, plus comparisons/report)
- Standalone Chrome runner in repo: `tools/run_browser_sharp_lite_chrome_compare.py` (requires Selenium and Chrome only when benchmarking; no production package added)

Remote mounted-Drive file copies were SHA256-verified, and Drive connector independently confirmed all eight evidence files. No raw source art was committed to GitHub.

### Decision and next goal

**Accept Sharp Lite as a browser-only opt-in candidate and close the independent mode implementation/evaluation stage. Do NOT automatically switch production's default profile.** The user can test the distinct `sharp` mode after a reviewed merge and verified deployment. Visual geometrization is improved, but minor stair-step contours remain; the next research goal is constrained straight-segment / corner optimization on the already shared arcs without modifying the Lite color hierarchy.

## 2026-10-08 release closure (supersedes earlier HOLD/deployment-pending references)

Sharp Lite PR #225 was merged into `main` (merge `f3313926c909458f90dbd7f48b26bac5e166dd8c`) and Shape v14 PR #226 was merged after retargeting `main` (merge `14657714960e639e7d669612ad19c265e0aefaea`). These are **production-shipped opt-in quality profiles**, not the new default and not Local Worker changes.

The Shin static host was updated with only `canonical-contour.js`, `browser-fallback.js`, and `app.js`. Public HTTPS byte-for-byte verification succeeded, and live Chrome 154 executed original Kyoko input for **Lite, Sharp, Shape, Exact**, all producing PNGs byte-identical to previously accepted predeployment baseline outputs with browser-u2netp guidance. No rollback was required.

See the authoritative [production handoff](../handoffs/HND-20261008-BROWSER_SHAPE_V14_PRODUCTION.md) and [Drive release evidence](https://drive.google.com/drive/folders/1WS4dLGFYol5VByP1bNPGMX0FwS4P9MGA) for SHA256 manifests, backups, public test output, and rollback instructions. Previous mentions of not-yet-merged / not-yet-deployed describe the development stage and are superseded by this release closure.
