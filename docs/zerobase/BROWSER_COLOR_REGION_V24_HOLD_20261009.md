# Minimalizer BrowserFallback v24: source-supported color-region boundary research

Date: 2026-10-09
Status: **RESEARCH STAGE COMPLETE; VISUAL-QUALITY PROMOTION ON HOLD**
Branch: `research/browser-color-region-v24-20261009` based on held v23 research PR #282.
Public production reference: Facet v15, untouched.

## Goal

After v17-v23 established guarded contour and region-merger research with almost no visible difference, v24 moves to **the original color-plane decomposition** of clothing, arms and hair, not just vertex count. The output intentionally omits eyes/nose/mouth. No generative painting, new colors or invented anatomy is permitted.

## Technique

1. Start with the exact original v15 Facet hierarchy, regions, 40-color-plane cut and source RGB. Do not modify the original image, region IDs, or final palette.
2. Enumerate 4-connected source pixels on the boundary between two existing adjacent regions. Calculate squared RGB error to the *current region's existing palette color* and to the *neighbor's existing palette color*. Admit a pixel as a candidate only when transferring it reduces source-color residual by at least 2,500 squared RGB units, both neighboring components are large, and three of its four neighbors remain donor-owned, one is recipient-owned. Restrict research to y>=33% of the image (garment/shoulder priority but not a semantic body-part classifier).
3. Rank deterministically by largest source-RGB improvement then pixel index. Moving 32 candidates in one batch produced an invalid canonical contour in the Kyoko real-image trial. Therefore the **accepted final v24 research setting allows exactly one source pixel per trial**.
4. Rebuild the exact existing connected component IDs/pixel ownership, retaining all palette RGBs, region IDs and region count. Construct canonical shared-boundary contours under existing Facet simplification, not new synthesis.
5. Fail closed: on any malformed contour loop, return the original unchanged Facet PNG with `rejected:invalid_contour`; on pixel-render divergence, zero-silhouette or long-thin protected-color violation, return the baseline. The final render allows at most 0.3% changed pixels, 0.55 mean RGB channel error and 0.2% largest individual-color mass difference. Any image failing the guard is unchanged.
6. Report `colorPlaneCandidates`, `colorPlaneMovedPixels`, `colorPlaneMoves`, source residual improvement and `colorPlaneQualityGate`. Research-only `?browserFallback=force&browserFallbackQuality=color` is available in the research branch. Production does not know this URL option.

## Real Chrome 154, original 340x340 sources

Actual JS `app.js requestBrowserFallback()` result was compared byte-for-byte to direct color engine output. Original Facet and Near PNG hashes match the accepted v22 reference. External pixel auditor tested representative green, gray left sleeve region, Noel's staff rectangle and brown mass, source/background white silhouette, all pixel change bounds and work-raster region statistics.

| Source | Boundary candidates | Source pixel moves | Source residual benefit (squared RGB) | Final changed PNG pixels | Contour vertex reduction | Facet / v24 time |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Kyoko | 383 | 1 | 146,245 | **0** | 0 | 4.28s / 6.41s |
| Noel | 578 | 1 | 84,215 | **8** | 0 | 4.57s / 6.69s |
| Ririka | 398 | 1 | 69,685 | **2** | 2 | 4.12s / 5.67s |

Pixel coordinates for the three candidates are Kyoko **(213,253)**, Noel **(289,276)** and Ririka **(170,209)**. All original 40 region IDs remain; existing accepted palette entries and all protected visual ROIs remain unchanged. All three final candidate gates report `pass`.

The initially attempted batch of 32 pixels on Kyoko produced `canonical contour loop has fewer than 3 points`, which exposed why local color-error benefit alone cannot be considered a valid geometric color-plane improvement. The code now reverts byte-identically to baseline on malformed contour instead of returning an error or publishing an invalid image. One-pixel trials yield valid polygons; this is a conservative engineering proof, not a redesigned sleeve/arm garment.

## Verification and decision

- Isolated Windows `tests/test_browser_color_region_v24.py` and all inherited v12-v23 modes: **66 PASS**. JavaScript and Python syntax pass.
- Real Chrome 154 three-character test and external source/palette/ROI benchmark: **3 PASS**.
- **GitHub Actions 11/11 PASS** on code-bearing commit `9cc40adfe7be5ab93151cb8eef80f251bc5a656f`: Color v24, Plane v23, Auto v22, Targeted v21, Donor v20, Merge v19, Near v18, Selective v17, Facet v15, Shape v14, Sharp Lite v13.
- Evidence and scripts: [Google Drive](https://drive.google.com/drive/folders/1lwNehPN4FYbHd3JzyZ1-RLc6P-gg-EpA) in the required short canonical `chatGPT及びCodex用/Minimalizer/ColorRegionV24_20261009` path. **Ten out of ten artifacts confirmed through Google Drive API**, with mounted-drive SHA256 verification against the original outputs. Includes the 3-source montage, original/source/baseline/output archive, metrics, tests and replay scripts.
- **Do not merge or deploy.** Research v24 proves one-pixel source-supported boundary correction and robust topology failure rollback, but modifies at most eight visible raster pixels and adds ~1.4-1.5x runtime. This does not reach the user goal of materially improved clothing internal colors and missing arm boundaries.

## Next phase recommendation

v25 must rework the *region representation* itself: identify source-supported broad garment/arm/hair planes before rendering, then propose small connected **groups** of boundary pixels while preserving graph connectivity and explicitly rejecting tiny loops/holes. Cache source segmentation and evaluate a candidate graph incrementally to prevent repeated full preprocessing. Require clear visual improvement across the same golden images, not just vertex count or source-RGB residual. Keep real staff/tie/sleeve and white silhouette invariants. Promote to main only after actual artistic quality and latency pass.
