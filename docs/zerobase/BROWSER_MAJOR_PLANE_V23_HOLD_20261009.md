# Minimalizer BrowserFallback v23: major color-plane contour refinement

Date: 2026-10-09
Decision: **RESEARCH COMPLETE / PRODUCTION HOLD**
Branch: `research/browser-major-plane-v23-20261009` based on held v22 research PR #234.
Production reference: unchanged Facet v15 on main.

## Intent

The previous v17–v22 studies showed reliable palette/silhouette protection, but removing same-color boundaries changed only 3 pixels in the best automatic v22 result while increasing runtime. v23 probes the actual polygon edge model, especially boundaries adjoining large hair, clothing or shoulder color regions. Intentionally omitted eyes, nose and mouth must remain omitted. Do not use img2img, generative fill or inferred facial content.

## Implementation

- Opt-in browser research profile `?browserFallback=force&browserFallbackQuality=plane`. No change to default Facet, Lite, Sharp, Shape, Exact, Near or Auto profiles.
- In `web/static/canonical-contour.js`, `plane-safe` uses the accepted Facet shared-boundary simplification and reruns more geometric trial edits *only for chains adjoining a region occupying at least 3.5% of the work raster*. Maximum proposed chord deviation 3.2px versus Facet 2.35px; stricter per-region IoU-loss threshold 0.0012 versus 0.0025; at most 24 trials/8 removals per eligible chain versus 14/5. Graph topology, shared-chain intersection and both adjacent regions' shape-fidelity gates stay active.
- `web/static/browser-fallback.js` builds the same Lite structure, superpixel hierarchy and color palette as Facet. It computes an independent Facet baseline and only accepts Plane if rendered vertices decrease, changed raster pixels stay ≤0.8%, mean RGB error ≤0.85, largest single-color mass change ≤0.4%, white/nonwhite silhouette remains exact, and all automatically detected narrow-color components stay unchanged. Any failure returns the original baseline Facet PNG.
- The v23 profile is separate from v22 Auto; it never merges region IDs or recolors palette entries. Research metadata expose `planeQualityGate`, `planeQualityChangedPixels`, and `planeVertexReduction` in both engine metadata and HTTP response.
- JavaScript path and script-level safety are tested independently in `tests/test_browser_plane_v23.py`; the unchanged older modes retain their inherited regression suite.

## Chrome 154 golden evaluation

Original 340×340 Kyoko GC001, Shirogane Noel and Ichijou Ririka inputs. Real `app.js requestBrowserFallback()` Plane profile output matches direct JS engine PNG byte-for-byte on each sample. Facet and Near PNGs independently match prior accepted v22 hashes.

| Sample | Gate | Regions | Facet → Plane vertices | Final pixels changed | Plane run time |
| --- | --- | ---: | --- | ---: | ---: |
| Kyoko | PASS | 40 | 1377 → 1361 | 11 | 6.52s |
| Noel | REJECT protected feature | 40 | 1232 → 1232 | 0 | 6.85s |
| Ririka | REJECT no vertex gain | 40 | 880 → 880 | 0 | 5.85s |

For the Kyoko accept, the global green RGB(149,211,27) pixel count remains 1,994 (this is *not* a hand-segmented tie mask); gray sleeve point (95,275) RGB(65,66,74), sleeve ROI, and white/nonwhite silhouette remain unchanged. Noel's characteristic staff ROI and exact RGB(68,37,36) mass are preserved in the returned PNG. Ririka's output is a byte-identical rollback.

## Outcome

v23 establishes the feasibility of more ambitious **large-plane straightening trials** without changing the source region partition, and verifies a real rollback when an important thin feature would change. Still, **16 fewer vertices and 11 changed pixels on one golden image is not visually meaningful enough to promote to production**. Image quality remains primarily constrained by the original region decomposition, color plane design and representation of the arm and clothing. More contour parameter tuning is unlikely to solve that by itself.

- Isolated Windows v12–v23 regression suite: **63 PASS**, JS syntax check PASS.
- Actual original golden PNG audit and ROI checks: **3 PASS**.
- GitHub CI `.github/workflows/browser-plane-v23.yml` and inherited suites: check conclusions explicitly before claiming PASS.
- Evidence location: [Google Drive v23 in chatGPT及びCodex用/Minimalizer](https://drive.google.com/drive/folders/1rAqWeEl1d7RKPs_laZVfkGg43Zc3BOQw). Includes source/Facet/Plane PNG comparison, JSON and CSV metrics, original inputs archive and reproducible Chrome scripts.

## Next phase (v24)

Do not continue endless region merges or simple vertex minimization. Quantify visibly meaningful **color-plane segmentation and garment/arm boundaries** at source and rendering levels. Develop targeted improvement to region decomposition without invented pixels, missing original arms, altered clothes or color drift, then run multi-golden comparison. Preserve fixed green, gray sleeve, Noel staff and silhouette gates. Performance must remain acceptable. Do not merge/deploy until verified visual improvement exists.
