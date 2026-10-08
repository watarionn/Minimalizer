# BrowserFallback v20: donor geometry distribution and bottleneck diagnosis

Date: 2026-10-08
Status: **RESEARCH STAGE COMPLETE; NO QUALITY GAIN; DO NOT MERGE/DEPLOY**
Branch: `research/browser-donor-distribution-v20-20261008`
Based on: held v19 draft PR #230, itself stacked on held v18/#229 and v17/#228.
Production reference: **Facet v15**, unchanged.

## Goal

Measure why 3 consecutive selective-merge research iterations accepted zero region merges without weakening their guards. The intended output remains simple geometric flat colors, with intentionally omitted eyes/nose/mouth. Kyoko's green tie and gray left sleeve must remain stable. Mass v16's indiscriminate 40→30 region cut changed 37%, 65%, 41% of Kyoko, Noel and Ririka pixels, so lowering a global region count is prohibited.

## Read-only implementation

- `web/static/browser-fallback.js`: optional `captureCandidateGeometry` probe records *every original adjacent pair* while leaving candidate admission, palette, segmentation, contour topology and raster generation unchanged.
- `web/static/app.js`: enables probe ONLY when using the experimental branch's `near` profile, not normal Lite, Sharp, Shape, Facet or Selective. No default changed.
- For each pair, record smaller donor region ID, recipient ID, donor pixel area, bounding box, bbox width/height, minimum width, aspect ratio, fill ratio, shared contact edges, contact/perimeter ratio, palette ID equality, source RGB and accepted palette RGB distances, and **11 independent boolean gate results**. The v19 first-failure category is separately retained; independent gate failures can overlap.
- `tools/run_browser_donor_v20_chrome.py`: Chrome 154 benchmark running **Facet and Near only**, plus the actual UI `app.js requestBrowserFallback()` route, with browser U2Netp guidance. No repeated seven-mode work.
- `tools/analyze_browser_donor_v20.py`: reproducible strict input checks, source/baseline SHA256 comparisons, candidate CSV, per-source quantiles/histograms, independent gate counts, strictly labeled *hypothetical* threshold sweeps and a diagnostic chart.

No new dependencies in browser, no generative fill, no Local Worker changes, no hosted inference. **No candidate parameter was relaxed.**

## Real Chrome benchmark

Same original 340×340 Kyoko GC001, Shirogane Noel and Ichijou Ririka image set as v15–v19; 40-shape output, identical preprocessing/contour/palette/subject guidance. Direct Near PNG and full UI route PNG match byte-for-byte. Both equal the original Facet v15 PNG, and the previous v19 Near PNG for every input.

| Source | Pairs | First-fail area OR shape | Independently failing donor area | Min-width fail | Aspect fail | Actual merges |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Kyoko | 87 | 76 | 74 | 2 | 0 | 0 |
| Noel | 81 | 74 | 70 | 4 | 0 | 0 |
| Ririka | 92 | 67 | 64 | 3 | 5 | 0 |
| **Total** | **260** | **217** | **208** | **9** | **5** | **0** |

- 217/260 first failures are the grouped donor area/geometry gate; the new independent tests resolve the overlap. The min-width and aspect columns must **not** be added to area failures as mutually exclusive groups.
- The hard donor area cap is **0.15% of the work raster**, about **173 pixels** for 340×340. Median donor areas of actual adjacent pairs: Kyoko **2,012 px**, Noel **1,199 px**, Ririka **668.5 px**. Median bbox minimum sides: **38**, **46**, **18 pixels**. Region size, not thinness alone, is the dominant first blocker.
- Source-RGB independent gate fails 249/260 pairs and accepted-palette-error gate fails 210/260 pairs, often masked by the earlier area rejection. In other words, relaxing just area does not make most candidates safe.
- 5 candidate **pairs** (Kyoko 3, Noel 2) satisfy all independent guards **except the donor area cap**. They correspond to only **four distinct donor regions** because one Kyoko donor is adjacent to two eligible recipients. All five pairs are **same accepted palette color**, with donors ranging from **3,857 to 6,738 pixels** (3.34–5.83% of the image). Ririka has no such pair.
- Raising the donor area cap from 0.15% to 2% while retaining every other guard yields **zero** admissible pairs. Those five require exceeding 3%, an unsafe jump if globally applied.
- All neighborhood comparisons were analyzed without merging even once. This means *none* of the five pairs is a proven visually safe merge; their size, internal connectivity and eventual outer contour must be checked after a one-merge render trial.

## v21 decision: targeted fixed-palette internal-boundary candidates

Do **NOT** indiscriminately loosen `maxSmallFraction`, source RGB, palette or silhouette gates, and do not count candidate pairs as distinct merge opportunities. Instead:

1. Run **one isolated same-palette pair** at a time, selected from the five measured pairs, explicitly identifying source donor and target IDs. A source- and destination-ID whitelist prevents a global threshold change.
2. Keep the palette fixed. Do not recolor any source pixel or introduce facial features. The aim is removing unnecessary **internal** borders between same-color regions, not deleting a region's visible signature.
3. Rebuild shared contours and topology, compare resulting PNG to the approved v15 PNG using v19's rendered pixel-change / color-mass gate, add **protected narrow-color-feature/silhouette ROIs**, and rollback the entire candidate on any failed check.
4. Validate Kyoko, Noel and Ririka after each experimental code change. A reduction of polygon records alone does not prove more geometric clarity if rendered pixels and visible corners do not improve.
5. If eliminating same-color internal boundaries yields no visible benefit, change course toward region-shape reconstruction rather than tuning merge thresholds indefinitely.

## Verification

- v20 probe-focused tests cover independent width/area/aspect flags, no-probe parity, deterministic pair counting, same-palette/contrast candidates and inability to override an existing reject.
- Isolated Windows Chrome 154 ran all three golden images, and all corresponding Facet/Near output PNGs remain SHA256-identical to previously accepted v19 outputs. Actual v20 Near browser app route equals direct engine byte-for-byte.
- Extended v12/v13/v14/v15/v17/v18/v19/v20 regression suite: **52 passed**. JS syntax PASS.
- GitHub Actions **7/7 PASS** on the code-bearing revision `2daf1edd39dc85c10313a6fd6acb27172d6c9c4a`: Donor v20, Merge v19, Near v18, Selective v17, Facet v15, Shape v14, and Sharp Lite v13. Earlier failures were caused solely by trailing spaces in this Markdown and were resolved. This documentation-only update does not alter tested runtime behavior.

## Preservation

All source PNGs, Facet/Near PNGs, raw Chrome results, source SHA256, 260 candidate records, independent-gate histograms, safe-counterfactual counts, report/chart and replay scripts are preserved in the mandated Google Drive project hierarchy:

[Google Drive Donor Distribution v20](https://drive.google.com/drive/folders/1kpUQykO0PXUNs_HGLC010q3j3z8JY7j0)

Under `chatGPT及びCodex用/Minimalizer/BrowserFallback_GeometryV13_20261008/ShapeV14_20261008/FacetV15_20261008/SelectiveV17_HOLD_20261008/NearColorV18_HOLD_20261008/MergeDiagnosticsV19_HOLD_20261008/DonorDistributionV20_20261008`.

**Ship decision: NO.** All changes stay on v20 research branch, separate from public main and Shin production, until actual visual gains and render-space fidelity are demonstrated.
