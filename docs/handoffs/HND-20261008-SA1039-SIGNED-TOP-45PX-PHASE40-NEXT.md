# HND-20261008 SA10.39 → SA10.40: protect source silhouette while cleaning interior SVG edges

**Canonical repo:** `watarionn/Minimalizer`.
**Working research branch:** `research/sa1032-svg-contour-proposals`.
**Pull request:** [#223](https://github.com/watarionn/Minimalizer/pull/223) **DRAFT / UNMERGED / NOT DEPLOYED**.
**Official SA10.39 measured report:** `docs/zerobase/SA10_39_SELECTIVE_SIGNED_TOP_EDGE_CHROME_20261008.md`.

## User priority

**Exterior silhouette already looks good.** Never destroy it to improve interior color or Chrome pixel metrics. Large gray garment trapezoid was corrected in SA10.36 using source-backed navy/white/green geometric polygons. Face eyes/mouth/nose are intentionally unrendered; left/right arms protected; thin green tie should not expand. No generative source image fill, pixel bitmaps in SVG, or source-owner data invention.

## Verified state

- SA10.37 isolated apparel layer Chrome mismatch 528, actual apparel shapes 5 and 27 vertices after simplification.
- SA10.38 luminance SVG mask and source-derived hole-edge outline passes cut mismatch to **69**, with **3 off-original-owner pixels**.
- SA10.39 initially considered an entire-source-owner white outline stroke: **56 Chrome-mismatched pixels**, BUT **22 off-owner pixels** (19 worse). **REJECTED** despite fewer total mismatches. The gate has explicit anti-silhouette-regression tests.
- Instead SA10.39 added an **opt-in SVG white stroke on only two already recorded horizontal parent polygon TOP edges**: coordinates (91,245)–(230,245) and (233,245)–(238,245). The code demands exact replay of the canonical rasterized source-owner top row before allowing this geometry. Stroke width 1.25px, x+0.5px, y+1.0px (GC001 research tuning only; not production default).
- Two new SVG paths, **four reused original contour endpoints**, counted. Previous five hole-border white stroke paths and original five colored garment polygons remain counted. Neither the original source polygon rings nor garment polygons/owners/palette/colors changed.
- Actual headless Chrome **45 differing RGB pixels**, **34 strong**, vs previous 69 / 51 and original 528 / 388; SA10.38→SA10.39 **34.7826% reduction**, SA10.37→SA10.39 **91.4773% reduction**.
- New **off-owner mismatch remains 3**, identical to SA10.38, unlike rejected 56px variant. **Top y245 row error 23→0**, with remaining 45 decomposed as **39 paint/blank** plus **6 wrong colors in joint paint**; **14 near both parent+material signed edge**, **31 near material edge only**, **zero** distant from either (1px margin). 28 small connected mismatch regions.
- Real Chrome executable SHA/HTML/SVG/screenshot SHA verified, 6 independently regenerated output hashes matched; 2 residual audit hash results matched. Original GC001 and Juufuutei-Raden source SHA distinct. Raden unrelated five-panel uniform remains unchanged.
- Cross-case **research gate PASS**, Chrome exact pixel parity **FAIL** (45 !=0), all total vector gates still **FAIL**. **120 extended local tests PASS + 18 parameterized subtests**; verify final GitHub Actions success before future promotion.
- No changes to main checkout, production BrowserFallback or worker; research PR #223 stays draft/unmerged.

## Engineering artifacts

- `tools/run_sa1038_vector_mask_browser.py`: new optional `--signed-top-edge-stroke 1.25 --signed-top-edge-y-shift 1.0`. This option is validated by source-ring raster replay; broad parent outline cannot be enabled simultaneously. The default stays zero.
- `tools/run_sa1039_svg_residual_audit.py`: strict SHA-qualified actual Chrome residual geometry attribution (cannot assume a PNG was rendered by Chrome).
- `tools/run_sa1039_edge_research_gate.py`: before+after real pixel diagnostic, silhouette overpaint nonregression requirement, extra SVG paint pass geometry accounting, Raden negative control, NO-GO.
- `tests/zerobase/test_sa1038_vector_mask_browser.py` with additional source top-edge tests; `test_sa1039_svg_residual_audit.py`; `test_sa1039_edge_research_gate.py`.
- `.github/workflows/sa1032-svg-research.yml` covered these plus preexisting full research tests.
- Data: `docs/zerobase/evidence/sa1039_*.json` in this branch.
- Binary + originals + comparisons + rejected global overpaint + four calibration scans + SHA manifest: `chatGPT及びCodex用/Minimalizer/SA1039_SelectiveTopSVG_20261008`
  https://drive.google.com/drive/folders/1AkmQG5r-cEU9uDrUInkUAnQlaEl_D7k0
  23 files original byte hashes verified on mounted Drive.

## Actual reproduction

With source path from existing SA10.34/SA10.37 handoffs, in isolated checkout:
```powershell
$env:PYTHONPATH='C:\Work\Temp\sa1033-checkout'
$py='C:\Work\Projects\Minimalizer\.venv\Scripts\python.exe'
& $py -m tools.run_sa1038_vector_mask_browser `
  --outer-scene 'C:\Work\Temp\sa1034-evidence\GC001_adaptive\phase8_adaptive_source_contour_research.json' `
  --apparel-scene 'C:\Work\Temp\sa1037-evidence\GC001\apparel_simplified_subpaths.json' `
  --apparel-metrics 'C:\Work\Temp\sa1037-evidence\GC001\apparel_simplified_metrics.json' `
  --signed-top-edge-stroke 1.25 --signed-top-edge-y-shift 1.0 `
  --output-dir 'C:\Work\Temp\sa1039-evidence\REPRODUCE'
& $py -m tools.run_sa1038_vector_mask_browser --render-chrome `
  --chrome-bin 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --output-dir 'C:\Work\Temp\sa1039-evidence\REPRODUCE'
```
Inspect `svg_material_parity_metrics.json`; it must stay **FAIL** until **0** pixel difference AND other hard gates are proven, not just a 91% decrease.

## Non-negotiable next-phase gates

1. Need **full-character actual Chrome SVG render** (not isolated apparel), identical source semantics, face/arms and z-index, independent positive second outfit. The current Raden is only a nonmatching negative control.
2. **45 actual remaining mismatches** must be reduced with no **off-owner** increase beyond SA10.38 (3). Target the 31 material-only diagonal-border errors and 14 overlapping parent/material edge errors; never trade silhouette for global pixel MSE.
3. Full original vector ring budget **GC001 3,604 >1,887, Raden 2,370 >1,412**. With inner SVG/material/holes geometry, combined budget is even tighter. No hiding subpaths, strokes or repeated points. Source topology and arms stay strict.
4. Maintain source-observed apparel palettes, thin center green tie and zero new facial features; seek explicit user visual approval on comparison PNG before merge.
5. GitHub and Drive remain canonical; RDC only to access local original image and actual Chrome when required, minimum calls. No deploy or PR merge until all original hard gates PASS.

**SA10.39 research engineering and evidence COMPLETE, strict production decision NO-GO.**
