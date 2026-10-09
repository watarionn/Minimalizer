# BrowserFallback v33: SVG source-bound contours and smoothing HOLD

Date: 2026-10-09
Status: **EXACT SVG/CHROME PARITY PASS / SMOOTHING HOLD**
Branch: research/browser-svg-contours-v33-20261009
Base: held v32 PR #304. Public Facet v15 / Local Worker unchanged.

## Goal and source contract

V32 produced irregular source-owned garment RGB planes for Kyoko, Noel and Ririka, with source/frozen Facet/class-map SHA-256 and protected identity color gates. V33 converts those existing research planes into actual SVG polygon paths, then evaluates contour simplification through the real Chrome SVG renderer. All original files are verified against v32 manifest. No new AI inference, generated image content or semantic part ownership.

The **hybrid** SVG embeds the unmodified frozen Facet PNG background and layers true SVG fill paths on top. It is NOT a fully vectorized character. Exact mode traces integer pixel-cell edges, supports nested holes, preserves 4-connected components and joins same-color contours with the even-odd fill rule. All fills are source-observed v32 RGB colors. Simplified mode uses cv2 approxPolyDP epsilon=1.1 pixels and is diagnostic only.

## Chrome verification at original 340x340

| Case | Exact SVG paths | Exact vertices | Exact raster mismatch | Simplified vertices | Simplified raster mismatch | Outside-allowed changes | Unsourced raster RGB values |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kyoko | 238 | 6088 | **0** | 1795 | 4400 | 518 | 2906 |
| Noel | 371 | 8976 | **0** | 2509 | 6608 | 920 | 3137 |
| Ririka | 301 | 12434 | **0** | 3310 | 8463 | 776 | 1681 |

Exact SVG in Chrome reproduces v32 byte-exact pixel data in all three cases. The exact mode has **zero** source mask overshoot, changed alpha, changed protected Kyoko tie/left-sleeve pixels, changed Noel staff pixels or unsourced rendered RGB. It is a safe **representation of the existing v32 research** and not independent garment/arm proof.

Simplification reduces contour vertices substantially but **FAILS quality/safety** in all three: significant raster changes, observed garment mask leakage and anti-alias-generated colors. It was NOT promoted. The original grayscale/facial limitations and source model garment/arm ownership ambiguity are unchanged. Do not imply the SVG is already smooth or a clean Bezier implementation.

## Implementation and tests

- tools/vectorize_browser_planes_v33.py: SHA-pinned manifest, 4-connected pixel-cell contour tracing, nested holes with even-odd winding, source RGB fills, exact and experimental approx mode.
- tools/audit_browser_svg_v33_chrome.py: Chrome renders two SVG variants per case; compares resulting RGBA, source palette, protected pixel/color mass, alpha and mask bounds against frozen v32.
- tools/verify_browser_svg_v33_replay.py: completely independent second Chrome run, 14/14 SVG/PNG/JSON artifacts SHA-256 byte-identical.
- tests/test_browser_svg_v33.py: seven new tests for holes, islands, exact polygon area, fail-closed source, research-only scope.
- Existing browser research CI extended to compile and test v33; no production asset, app routing or Local Worker modifications.

The standalone SVG includes an embedded background raster; its SVG paths genuinely encode color-plane boundaries. It is not a source-native full vector character model.

## Next

V33 **vector representation complete; contour smoothness and production HOLD**.
Next research should use per-component geometric rollback, true shared-edge topology constraints and pixel-safe SVG raster analysis so a simplified contour can be accepted only after zero outside-mask/protected changes and original-source palette checks. Do not waive tests for apparent visual improvement. Reliable left/right arms and accessory/garment evidence still need independent semantic verification. No image generation or invented facial internals.

Preserve under Google Drive chatGPT及びCodex用/Minimalizer/SvgContourV33_20261009.
