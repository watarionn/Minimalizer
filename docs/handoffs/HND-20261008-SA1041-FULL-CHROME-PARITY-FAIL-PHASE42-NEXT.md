# HND-20261008 SA10.41 → SA10.42: full-character Chrome parity, signed owner masks

**Canonical source:** `watarionn/Minimalizer`, branch `research/sa1032-svg-contour-proposals`, draft PR [#223](https://github.com/watarionn/Minimalizer/pull/223). **No merge, no deployment.**

**Completed full report:** `docs/zerobase/SA10_41_FULL_CHARACTER_BROWSER_VALIDATION_20261008.md`.

## Most important new finding

The previous four phases proved genuine *isolated five-panel clothing* Chrome color-edge improvements (**528→69→45→41** different pixels), not full-character vector parity.

SA10.41 now **reconstructs both original full-image signed Phase37 PNGs in OpenCV, pixel-for-pixel**, then **really renders the complete 11-owner source vector scene in Chrome**.

- GC001: Phase9 3 observed inner planes + Phase37 5 apparel planes / 27 vertices. Original full preview pixel-exact reconstructed PASS. Browser differs **3,919 pixels**, including face **140**, left arm **206**, right arm **199** inside original Stage04 protected masks. Source contour **110** singleton/two-point rings.
- Raden: Phase9 1 inner plane + Phase37 **0 apparel** (correct nonmatching no-op). Original full preview pixel-exact reconstructed PASS. Browser differs **2,681 pixels**, including face **122**, left arm **237**, right arm **255**. Source contour **13** tiny rings.
- Original outer ring vertex hard limits from signed Stage8 metrics: GC001 **3,604 vs 1,887**, Raden **2,370 vs 1,412**. Combined owner/stage04 guard/stage9/stage37 SVG vertex occurrences **4,312** GC001, **2,976** Raden, so **DO NOT CLAIM vertex budget pass**.
- Original Source Stage04 face guard is **flat, source-observed face color**; not a facial feature generator. The SVG includes original Stage04 face and arm masks converted into counted vector paths, not embedded PNG.
- SVG small source contours: 1pt becomes explicitly counted 1×1 geometric rect, 2pt becomes explicitly counted SVG line. No dropped data; nevertheless **SVG even-odd vs OpenCV cv2.drawContours inclusive fill semantics are not pixel-identical**.
- Both Chrome runs independently repeated: **7 of 7 exact SHA256 file matches per character**. Distinct source SHA, isolated actual Chrome, verified input/output SHA lineage. Two-case **research evidence PASS**, full Chrome/browser-face/arms/budget **FAIL**.
- Local regression **145 passed + 54 parameterized subtests**, Python compilation PASS. Check final GitHub Actions head run to confirm CI status.
- Drive `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008`: **25 hash-verified files and manifest**. [Browse full SVG and before/Chrome/heatmaps](https://drive.google.com/drive/folders/1-S22L7dMzs7tH32aLMel5bTSSsTQY7Oi).

## Actual modules (GitHub)

- `minimalizer_zerobase/reviewed_sa10/full_character_svg.py`: all signed owner masks back-to-front, short/long rings, Stage04 face+arm shields, flat face guard, Stage9 inner colors and Stage37 apparel, geometry budget accounting.
- `tools/run_sa1041_full_character_chrome.py`: source SHA+saved PNG authority, exact canonical OpenCV reconstruction, SVG/HTML output, real headless Chrome and pixel/face/arm difference stats.
- `tools/run_sa1041_full_scene_crosscase_gate.py`: two independent original SHA + negative Raden/no-go gates.
- `tests/zerobase/test_sa1041_full_character_svg.py`, `test_sa1041_full_scene_crosscase_gate.py`.
- `.github/workflows/sa1032-svg-research.yml`: new tests/tool compilation.
- `docs/zerobase/evidence/sa1041_gc001_full_character_chrome_20261008.json`, `sa1041_raden_full_character_chrome_20261008.json`, `sa1041_two_source_full_character_gate_20261008.json`.

### Reproduction (isolated research checkout only)

Existing local isolated checkout `C:\Work\Temp\sa1033-checkout` may be fetched at research head. Venv `C:\Work\Projects\Minimalizer\.venv\Scripts\python.exe`. For GC001:
```powershell
$env:PYTHONPATH='C:\Work\Temp\sa1033-checkout'
$py='C:\Work\Projects\Minimalizer\.venv\Scripts\python.exe'
& $py -m tools.run_sa1041_full_character_chrome `
  --scene 'C:\Work\Temp\sa1034-evidence\GC001_adaptive\phase8_adaptive_source_contour_research.json' `
  --stage9-dir 'C:\Work\Temp\sa1035-evidence\GC001' `
  --stage37-dir 'C:\Work\Temp\sa1037-evidence\GC001' `
  --stage04-dir 'C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_04' `
  --source 'C:\Work\Temp\macro-gc001\GC001_source.png' `
  --output-dir 'C:\Work\Temp\sa1041-evidence\GC001'
& $py -m tools.run_sa1041_full_character_chrome `
  --render-chrome --chrome-bin 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  --output-dir 'C:\Work\Temp\sa1041-evidence\GC001'
```
Do NOT interpret the successful command or canonical source replay as a Chrome parity PASS: inspect `full_character_svg_metrics.json` for per-owner protected FAIL and actual Chrome errors.

## Next engineering phase SA10.42: prioritized acceptance gates

1. **Per-owner SVG pixel replay diagnosis**, starting with both left/right arms, face and hair. Render each signed source owner alone, compare canonical `rasterize_primitive_candidate` with actual Chrome vector masks. Record 1pt,2pt,all-path,even-odd hole and line-end contributions. Do not use PNG overlay or unknown fake geometry to pass.
2. **Source-protected face/arm exact parity** is stronger than global similarity: require 0 different pixels inside Stage04 face/left/right arm masks in Chrome, or explicit HOLD. Do not merely declare source masks immutable; actual Chrome screenshot must match.
3. Test composition/z-order separately once individual owner SVG parity passes. Keep 11 owner back-to-front records, original structural-only head, Stage9 original observed palettes and flat source face guard.
4. **Original ring vertex budgets remain mandatory** (GC001 1887, Raden 1412). Track all duplicated mask/face/inner paths in combined geometry. Investigate equivalence-preserving simplify/merge without sacrificing face/arms or silhouette.
5. No independent second positive five-material outfit yet. Raden is a negative no-op, not apparel generalization. Human visual approval pending.
6. **Research PR #223 stays draft.** Production worker/browser fallback/main untouched. Preserve all code on GitHub and visual/evidence on Google Drive under `chatGPT及びCodex用`. Use RDC only for original images/actual Chrome, not by default.

**SA10.41 complete as a research/diagnostics engineering milestone. Product release is explicitly NO-GO.**
