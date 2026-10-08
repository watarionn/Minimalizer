# BrowserFallback Near-Color Selective Merge v18: research gate

Date: 2026-10-08
Status: **HOLD_NO_GEOMETRY_GAIN** (research only; no production merge or deploy).
Branch: `research/browser-near-color-v18-20261008`, based on unmerged v17 research branch.
Only BrowserFallback; no Local Worker, no image synthesis or new packages.

## Goal / why

The user wants cleaner geometric color regions while preserving the deliberately omitted face features. Arbitrarily cutting 40 regions down to 30 in v16 changed 37.07%/64.53%/40.83% of Kyoko/Noel/Ririka pixels. v17 restricted merges to same-palette neighbors and safely accepted zero among 87/81/92 adjacency pairs. v18 investigates *nearby palette IDs* without allowing the green tie to grow or sleeve gray to turn navy.

## Prototype

Experimental opt-in `?browserFallback=force&browserFallbackQuality=near` exists only on this isolated branch.

After Facet v15's 40-region hierarchy and fixed palette are created, each adjacent source-region pair can be evaluated for merging. Unlike v17, it permits different palette IDs **only if all existing spatial/color/shape guards plus explicit additional recoloring limits pass**.

- Preserve source `l0-lite-jacobi`, shared canonical arcs, Facet geometry, 2x OpenCV raster. Keep all previous modes unchanged.
- Donor region must be compact, tiny (0.15% of pixels or less), min bounding side 5px, aspect ratio ≤3, with ≥5 shared pixel-edges and shared boundary coverage ≥18% of donor-box perimeter.
- Source RGB mean Euclidean difference ≤16. For different-palette pairs, palette RGB Euclidean difference ≤18, max tolerated error 8, and recolored source-label budget ≤0.15% of image area. The 8-unit limit is conservative and currently stronger than 18.
- Max 2 deterministic merges. Recipient palette remains unchanged, donor palette is not recomputed. Every generated region maintains complete pixel ownership, and existing downstream shared-contour topology and IoU safeguards remain.
- Count inspected near-palette pairs, color-fidelity rejections and accepted recolor pixels. Invalid spectral/contour combinations fail closed.
- This is an *exploratory prefilter*, not a full output-space proof. It does not yet raster-render every candidate against the baseline before commit. A candidate that passed this filter would still require an independently checked PNG/ROI fidelity gate before promotion.

## Real Chrome 154 benchmark: three sources

All sources are original 340×340 Kyoko, Shirogane Noel and Ichijou Ririka used in verified Facet v15 and v17 comparisons. Browser subject guidance and image processing settings were unchanged. The actual `app.js requestBrowserFallback()` path produced the exact same PNG bytes as direct v18 engine invocation for every source.

| Source | Total neighbor reviews | Near-palette candidates | Rejected by color gate | Accepted merges | Regions | Output vs Facet |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Kyoko | 87 | 76 | 11 | **0** | 40 | SHA256-identical |
| Noel | 81 | 69 | 6 | **0** | 40 | SHA256-identical |
| Ririka | 92 | 65 | 22 | **0** | 40 | SHA256-identical |

Prior Lite, Sharp Lite, Shape, Facet, Selective and Exact outputs were individually confirmed SHA256-identical to v17 baseline on all three sources.

Kyoko's representative green palette remains RGB(149,211,27) at 1,994 pixels. The left sleeve reference pixel at (95,275) remains RGB(65,66,74). Green count is a full-image representative RGB count, **not** a hand-segmented necktie area.

Synthetic unit fixtures verified that cross-palette merges can be admitted under an explicit safe-area override and that changed-area budgets, too-distant palette colors, and the v17 strict same-palette mode are protected. The synthetic fixture does not establish benefit on real characters.

**Conclusion:** This is a verified safe no-op on our three character samples, **not a quality improvement**. Do not merge into main, expose the public near mode or adjust production defaults. In particular, do not relax thresholds only to force the region count downward.

## Tests / evidence

- `tests/test_browser_near_v18.py`: opt-in and safe default, synthetic near-palette acceptance, over-budget and contrast rejection.
- Existing `test_browser_selective_v17.py`, `test_browser_facet_v15.py`, `test_browser_shape_v14.py`, `test_browser_sharp_lite_v13.py` inherited contracts updated only for additional explicit mode routing, without changing geometry/color expectations.
- `tools/run_browser_near_v18_chrome_compare.py`: reproducible live Chrome 7-mode evaluation harness for local research site only.
- CI: `.github/workflows/browser-near-v18.yml`. **GitHub Actions 5/5 PASS** on research PR #229: Near v18, Selective v17, Facet v15, Shape v14, Sharp Lite v13. These are engineering safety checks, not evidence of real-image geometry improvement.
- [Drive evidence folder](https://drive.google.com/drive/folders/1hHQ2sv0FiRVE77VMR1vfUWeAJWa9xeXV) under `chatGPT及びCodex用/Minimalizer`: three-source comparison montage, JSON, report and archive containing source and all seven output profiles.

## Next research gate

Before extending into a production improvement, instrument why candidate pairs fail (size/compactness, boundary length/strength, source RGB, palette RGB, changed-area cap), and add per-candidate **render-space** baseline comparison and rollback. Region count by itself is never an acceptance criterion. Keep thin colored traits protected without drawing eyes/nose/mouth. A candidate is promoted only when at least one real character gains a simpler region with independently verified silhouette, color and border invariants, and no tested regressions.

The [Facet v15 production handoff](../handoffs/HND-20261008-BROWSER_FACET_V15_PRODUCTION.md) remains authoritative for the currently deployed public quality modes. v17 and v18 are research branches.

## Final review and ship decision

Local extended suite **46 passed**, including v12, v13, v14, v15, v17 and v18. The three-source actual Chrome benchmark showed 0 admissible merges, no color regression and SHA256-identical Facet PNGs. Google Drive evidence files were SHA256-verified on the mounted target and independently listed through Drive. Consequently **HOLD_NO_GEOMETRY_GAIN**, PR #229 stays **Draft**, unmerged and undeployed. Public Shin production remains Facet v15.
