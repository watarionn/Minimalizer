# Handoff: BrowserFallback Facet v15 production verified (2026-10-08)

Status: **PRODUCTION VERIFIED**. Browser-only **opt-in** new `facet` quality profile. The existing Lite default, Sharp Lite, Shape v14 and Exact remain unchanged; owner Local Worker and ZeroBase2 are not modified.

## Goal

Reduce the residual stair-step edges in flat geometric color fields. Omission of eyes, nose and mouth is intentional. Preserve the Lite region ownership and palette, avoiding the tie-green expansion and left sleeve recoloring originally observed in Exact.

## GitHub

- Repository: `watarionn/Minimalizer`
- Facet v15 PR [#227](https://github.com/watarionn/Minimalizer/pull/227), merged to `main`
- Verified release code commit: `0f83b5ad91482dc1afe766955ca53f9072c9604b`
- Implementation: `web/static/canonical-contour.js`, `web/static/browser-fallback.js`, `web/static/app.js`
- Replay and regression: `tools/run_browser_facet_v15_chrome_compare.py`, `tests/test_browser_facet_v15.py`
- Design, algorithm limits, regression and benchmark: `docs/zerobase/BROWSER_FACET_V15_20261008.md`

## Architecture and safety

- `facet` uses Lite `l0-lite-jacobi` preprocessing, colors and owners, existing canonical shared arcs, and OpenCV-compatible 2x fill.
- Builds on Shape v14. Incrementally deletes interior vertices to replace nearby segments with a single straight chord, with fixed shared arc endpoints. No new colors, imagery, learned reconstruction, or server inference.
- Raw boundary corridor limit 2.35 px, angular near-45-degree preference (not forced snapping), hard protection of meaningful corners with at least 55-degree bends and at least 3.5 px straight support on both sides.
- Existing self-intersection, connected components/holes, area, centroid, directional extent, and minimum region IoU ≥0.90 safeguards remain; extra chain-local baseline IoU decline limit 0.0025. Maximum 14 evaluated candidates/5 deletions per arc.
- **Corrected regression:** the initial implementation measured only the two immediate edge lengths and could fail to protect a significant right angle subdivided into short collinear edges. Fixed by measuring collinear *support runs*. A synthetic test now covers the case. Real-image benchmark fully repeated after the fix.
- All earlier modes are independent and output-identical by SHA-256. The `facet` profile is explicit opt-in only. The default public browser route is still Lite.

## Verified development quality (Chrome 154)

Original 340×340 Kyoko GC001, Shirogane Noel and Ichijou Ririka input PNGs, equal 40-shape budget and equal palette/SLIC settings, no Local Worker:

| Source | Shape v14 vertices | Facet v15 vertices | Reduction | Facet minimum region IoU | Changed pixels vs Shape |
| --- | ---: | ---: | ---: | ---: | ---: |
| Kyoko | 1513 | 1377 | 9.0% | 0.90206 | 0.0848% |
| Noel | 1366 | 1232 | 9.8% | 0.90294 | 0.2318% |
| Ririka | 976 | 880 | 9.8% | 0.90074 | 0.1237% |

Kyoko dominant green RGB(149,211,27) area: **1994 pixels**, exactly matching Sharp/Shape. This is a representative palette color count across the entire output, not an isolated necktie polygon. Left sleeve at (95,275) retains **RGB(65,66,74)**. In Exact, the corresponding sampled sleeve was RGB(32,42,80), and its different dominant green covered 4111 pixels.

- **47 passed** on the isolated-release browser suites; JS and Python syntax checks pass.
- GitHub Actions Facet v15, Shape v14 and Sharp Lite v13 all passed on PR.
- Old Lite/Sharp/Shape/Exact PNGs matched accepted v14 baseline exactly on all three sources.
- `requestBrowserFallback()` UI route PNG was byte-identical to direct Facet engine on all three inputs.
- Remaining minor boundary stair steps are real. Do not claim finished vector perfection.

## Production shipping / read-after-write

Public origin: https://cf278796.cloudfree.jp/minimalizer/

Facet opt-in URL:
https://cf278796.cloudfree.jp/minimalizer/?browserFallback=force&browserFallbackQuality=facet

Production hosts browser code on Shin Free Server under:
`/cf278796.cloudfree.jp/public_html/minimalizer/static/` (FTPS view).

- Independently cloned `main` at the release commit and built `dist/shin` with `scripts/build_shin_static.py`. ONNX and ONNX Runtime WASM included in the build.
- Before write, public HTTPS JS files were verified **byte-equal** to the prior v14 release. Fetched and backed up the exact existing server files over the saved WinSCP FTPS session.
- Saved SHA256-checked backups and predeployment manifest to Drive **before** update.
- Binary-uploaded **only** `canonical-contour.js`, `browser-fallback.js`, `app.js`, in that order. No directory removal, no recursive sync, no model/WASM changes, no Local Worker restart.
- Public HTTPS fresh downloads of all 3 scripts were byte-identical to build, returned HTTP 200 with proper JS MIME:
  - `canonical-contour.js`: SHA256 prefix `cffa08b98f43a017`, 53638 bytes.
  - `browser-fallback.js`: SHA256 prefix `0a71a9eddef0d98f`, 144659 bytes.
  - `app.js`: SHA256 prefix `62d79d21619837c0`, 31100 bytes.
- Public page, Browser Subject JS, ONNX Runtime `.mjs`, WASM, and ONNX model all responded HTTP 200 with expected MIME types.

## Actual live public Chrome acceptance

Loaded live origin in Chrome 154, used URL `?browserFallback=force&browserFallbackQuality=<profile>`, supplied the original Kyoko source, invoked actual `app.js requestBrowserFallback()`, checked `browser-u2netp` guidance, correct quality/profile headers and PNG byte-for-byte equality with the previously accepted benchmark:

| Profile | Live PNG SHA256 | Result |
| --- | --- | --- |
| lite | `8b9c86f4549f60921103c9743f0c1127e04ed43a1d8c2d5e3961a9a11157c73e` | PASS |
| sharp | `c278f6081c6161b669be826eb9b28258488faea2859112d4227f19807d77f3ad` | PASS |
| shape | `fb97bf932c1e24d132987bbd6360b44227fce3992b0d15a8cd11c67cfb7950e2` | PASS |
| **facet** | `b1fcd2a0a6a7957e7ebec80412ec2e276bab9ce81ef82f4d5776d2d16a4fd539` | **PASS** |
| exact | `d67b7eb186c9659764e0030d9b3a3ae1df95722ea42deafc22fc9e01fb15013e` | PASS |

Facet live headers reported `x-minimalizer-contour-geometry-mode=facet-safe` and **68** additional removed vertices for Kyoko. All five produced exact benchmark PNG bytes, not merely successful HTTP responses.

## Evidence, rollback, next work

Google Drive canonical root, under `chatGPT及びCodex用`:
[Facet v15 source and comparisons](https://drive.google.com/drive/folders/1LkGY8T-yayAjHIzRSi3CHbdcT4MPY5mI).

[Facet production release and exact rollback backup](https://drive.google.com/drive/folders/18i2iowA2XJR6vTgdx1NDRRgNAG8-a26d).

The release folder contains original remote JS binaries, predeploy hash manifest, HTTPS integrity JSON, 5 live Chrome PNG outputs and metadata, verification scripts, and a release report. To roll back if later necessary, upload backed-up `app.js`, `browser-fallback.js`, then `canonical-contour.js` using explicit binary FTP operations, and verify public HTTPS hashes plus actual browser output afterward. **Rollback was prepared but not executed.**

Further geometric work should focus on bigger region-shape design, not simply vertex counts: geometric edge continuity, meaningful silhouette readability and minimal palette stability. Do not reinterpret this browser release as a Local Worker quality promotion.
