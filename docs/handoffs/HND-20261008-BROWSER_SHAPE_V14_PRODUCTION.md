# BrowserFallback Sharp Lite v13 + Shape v14 | Production release closure

Date: 2026-10-08
Status: **PRODUCTION SHIP VERIFIED** (browser-only opt-in profiles)
Source GitHub repository: `watarionn/Minimalizer`
Code source main release commit: `14657714960e639e7d669612ad19c265e0aefaea`
Public URL: https://cf278796.cloudfree.jp/minimalizer/

## Goal and scope
Introduce browser-only, crisp shared-boundary geometrization while keeping original Lite structural preprocessing and palette regions. The user's Kyoko concern is necktie green-area expansion and left-sleeve recoloring in Exact/Geo; Shape must avoid both. Eyes/nose/mouth omission is intentional. No generated imagery, no Local Worker logic change and no Railway runtime dependency.

## Integration
- PR #225 Sharp Lite merged into main: `f3313926c909458f90dbd7f48b26bac5e166dd8c`.
- PR #226 Shape v14 (stacked on Sharp Lite) retargeted main and merged: `14657714960e639e7d669612ad19c265e0aefaea`.
- `git clone --branch main` isolated checkout confirmed release SHA exactly.
- Static builder: `python scripts/build_shin_static.py` created `dist/shin` with index, JavaScript, ONNX model and WASM runtime.
- Release regression: 42 passed (Browser Fallback v12, Railway graduation v12, Sharp Lite v13, Shape v14), plus JS syntax checks pass.

## Production risk control
- Pre-release `app.js`, `browser-fallback.js`, `canonical-contour.js` from public HTTPS differed from pre-merge GitHub main **only in CRLF vs LF line endings**; normalized line content was identical for each.
- Downloaded exact binary remote copies through the existing saved WinSCP FTPS session **before** any write. Verified rollback backups against pre-merge GitHub source after newline normalization.
- Saved old binary files and predeployment hashes in the designated Drive hierarchy before uploading.
- Uploaded **only** `canonical-contour.js`, `browser-fallback.js`, `app.js` in that order, by explicit binary FTPS PUT. No recursive sync, no deletion, no .htaccess edits, no model/WASM modifications, no Worker changes.
- Remote FTPS path: `/cf278796.cloudfree.jp/public_html/minimalizer/static/`.
- The temporary FTP session initially opened in the unrelated `portfolio-city` folder; read-only `ls` discovered the correct path. No writes to other sites.

## Public HTTPS read-after-write
Each changed JS downloaded from the production URL with a cache-busting query and `Cache-Control:no-cache`. Actual byte content and SHA256 matched the release build:
- `canonical-contour.js`: SHA256 `865d1ce67315a98c...`, 46,420 B
- `browser-fallback.js`: SHA256 `5c931a629654b021...`, 143,709 B
- `app.js`: SHA256 `18bdf1b5f4efaac6...`, 30,801 B

All returned HTTP 200 with JavaScript MIME.
Public index, Browser Subject JS, ONNX Runtime ES module, ONNX model and WASM also returned HTTP 200, with correct `.mjs` / `.wasm` / `.onnx` content types.

## Real public Chrome smoke
On live HTTPS origin, loaded the actual UI `?browserFallback=force&browserFallbackQuality=<mode>`; verified profile routing, supplied original 340x340 Kyoko source, invoked the actual `requestBrowserFallback()` in Chrome 154, and checked the generated PNG against previously accepted source-local Shape v14 Chrome benchmark **byte-for-byte**:
- `lite` PASS, SHA256 `8b9c86f4549f6092...`, independent rings + Canvas.
- `sharp` PASS, SHA256 `c278f6081c6161b6...`, Lite preprocessing + shared arc + OpenCV 2x.
- `shape` PASS, SHA256 `fb97bf932c1e24d1...`, Lite preprocessing + corner-aware shared arc + OpenCV 2x.
- `exact` PASS, SHA256 `d67b7eb186c96597...`, spectral Exact as before.
- Subject guidance header was `browser-u2netp` on all four.
- Browser-generated PNG SHA256 equality and shape-mode-specific geometry header checked in automated script. No Local Worker was invoked.

## User-observed color regression guard
Real Kyoko benchmarks:
- Sharp and Shape both preserved RGB(149,211,27) green dominant mass at **1,994 pixels** (Exact had different green at 4,111).
- Left sleeve sample at (95,275) remained RGB(65,66,74) in Lite/Sharp/Shape; Exact had RGB(32,42,80).
- Shape trimmed 12.4%, 13.3%, 11.9% rendered vertices relative to Sharp on Kyoko, Noel, Ririka respectively, without exceeding the topology/IoU gates.

The dominant green mass is not a manually isolated necktie polygon. Pixel-level release checks are stronger: Shape/Sharp PNGs matched the accepted baseline exactly.

## Rollback and change boundary
If later release health regresses, recover exact backed-up JS files (preserved in Drive) through binary FTPS PUT. Apply in **app.js → browser-fallback.js → canonical-contour.js** order, then verify public HTTPS hashes and live browser behavior. This rollback was prepared but **not executed**; it was not needed.

The default Lite profile and old Exact are unchanged. New modes are opt-in with:
- `?browserFallback=force&browserFallbackQuality=sharp`
- `?browserFallback=force&browserFallbackQuality=shape`

A pre-existing v5 spectral test hard-codes `browser-fallback-v11` even though main is v12. The comprehensive extended suite previously showed 37 pass / 1 deselected. Release-specific 42-test suite is fully green, and the stale test remains separate technical debt.

## Evidence locations
- GitHub design: `docs/zerobase/BROWSER_SHAPE_V14_20261008.md`.
- Drive: `chatGPT及びCodex用/Minimalizer/BrowserFallback_GeometryV13_20261008/ShapeV14_20261008/ProductionRelease_20261008`.
- Public HTTPS integrity JSON, public Chrome smoke JSON, four result PNGs, original remote rollback JS files, predeployment manifest and production smoke script reside in that folder.

## Next
Return to quality R&D for the remaining coarse stair steps in a separate feature PR. Do not conflate this successful browser-only opt-in release with switching Local Worker model, making Shape the public default, or eliminating geometric artifacts completely.
