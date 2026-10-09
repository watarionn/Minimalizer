# BrowserFallback v34: local rollback and lossless SVG path compression

Date: 2026-10-09
Status: **CHROME EXACT PARITY + SVG BYTE REDUCTION PASS / SMOOTHING HOLD**
Branch: research/browser-svg-local-rollback-v34-20261009
Parent: Draft v33 PR #306, not main. Public Facet v15, Local Worker untouched.

## Goal and design

v33's exact hybrid SVG garment contours (unchanged embedded Facet PNG under actual vector paths) have zero Chrome pixel mismatch with v32, but naive polygon smoothing created unsourced blended RGB and outside-mask changes. v34 keeps exact original SVG color-group paths and a **real Chrome per-group rollback check**.

It parses SHA-verified v33 hybrid SVG color groups and loops (with even-odd holes), rewrites absolute line commands as shorter relative horizontal/vertical/diagonal commands with **identical path vertices**, then attempts epsilon=0.85px polygon simplification on 25 promising groups per Golden case. Every proposal is rendered into a real 340x340 Chrome RGBA canvas against the exact original frozen v32 PNG. A changed pixel, a bad protected color, alpha change, out-of-mask color or any browser error causes rollback of that single color group. The final full scene is rendered and must match v32 byte-for-byte, or all proposals are discarded.

This is an offline **hybrid** source-RGB research artifact; it is neither a pure vector character nor a new browser image generator. The garment-class and arm semantics are still unbound. All input images and v33 SVG are verified by archived SHA-256 manifests. No new model inference.

## Real results

| Case | v33 exact SVG bytes | v34 SVG bytes | Reduction | Contour vertices (before = after) | Group proposals tested | Accepted | Rolled back | Chrome pixel mismatch |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Kyoko | 72,429 | 41,040 | 43.34% | 6,088 | 25 | 0 | 25 | **0** |
| Noel | 99,453 | 54,335 | 45.37% | 8,976 | 25 | 0 | 25 | **0** |
| Ririka | 121,751 | 57,641 | 52.66% | 12,434 | 25 | 0 | 25 | **0** |

**The SVG gets shorter, but not geometrically smoother.** Zero accepted simplified contours! All 75 trial geometry changes were unsafe and automatically rolled back. The SVG byte reduction came entirely from lossless path syntax. No suggestion of accepted Bezier or shared-edge reconstruction.

Because Chrome final RGBA was **exactly identical** to v32 on all three cases, no output silhouette, Kyoko tie/left sleeve, Noel staff, RGB palette or alpha changed. Source mask and original Face/Arms uncertainties are unchanged. Source RGB and foreground preservation cannot establish semantic ownership, and no parts were fabricated.

## Verification, provenance and preserved outputs

- tools/optimize_browser_svg_v34.py: strict SHA-gated inputs, source color-group parser, relative path encoding, per-group proposals and real Chrome rollback, whole-scene fail-closed exact parity.
- tools/verify_browser_svg_rollback_v34.py: independent second Chrome run, **7/7 exact SHA-256 outputs** (three SVG, three real Chrome PNG, JSON) and pixel equality with the v32 raster.
- tools/summarize_browser_svg_v34.py: independent comparative gallery (original, exact v33, safe v34 and rejected v33 smoothing) and compact CSV.
- tests/test_browser_svg_rollback_v34.py: seven synthetic tests including path/holes, positive and negative group decisions, exception rollback and unchanged production routing.
- Existing Browser v25–v33 CI workflow extended. No new production dependency or UI route.

The comparisons, measured results and manifest live under canonical Drive folder:
chatGPT及びCodex用/Minimalizer/SvgLocalRollbackV34_20261009.

## Decision / next

**v34 per-group rollback and SVG byte compression PASS; accepted smoothing/vertex simplification HOLD.** v35 should test geometry simplification that can pass independent Chrome exact pixel/source-mask checks, perhaps component-wise edge ownership and local safe raster constraints. Do not lower protected tie, arm, staff, alpha or palette gates; do not call byte compression a geometry quality improvement.

No main merge, no Public deploy, no Local Worker change, no img2img or generated facial/internal anatomy. Old 5GiB free-memory policy stays removed per user instruction.
