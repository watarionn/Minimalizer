# BrowserFallback v21: explicit same-palette candidate and rendered rollback

Date: 2026-10-08  
Status: **RESEARCH PASS / PRODUCTION HOLD**. No main merge or Shin deployment.  
Branch: `research/browser-targeted-v21-20261008`, stacked on v20 / v19 / v18 / v17 research drafts.  
Production canonical: verified Facet v15. This work does not alter default Lite, Sharp, Shape, Facet, Near or Exact outputs.

## Goal / scope

After v20's geometry distribution found five **specific** large donor/recipient adjacency pairs (three Kyoko, two Noel), try ONE named same-palette pair at a time, avoiding global 40→30 cuts. Validate rendered shape/palette and undo rejected candidates. The design omits eyes, nose and mouth intentionally; never hallucinate or repaint character features. Browser-only, no Local Worker.

## Implementation and invariants

- `web/static/browser-fallback.js` accepts research-only `selectiveMergeOptions.targetedPair={donorId,recipientId}` in `_core.analyzeRgba`/the existing `minimalizeFile` path. No public URL or new default mode enables it.
- It requires exact donor and recipient IDs, real adjacency, donor as the smaller component, both regions having the **same accepted palette ID**, `allowNearPalette=false`, `maxMerges=1`. The only bypass is **donor area** for the explicitly named pair, capped independently at **6%** of the full analysis raster. No global area-cap relaxation.
- Min side, aspect, source RGB closeness, shared edge and shared-perimeter ratio gates remain enforced. Palette entries and representative color assignments are held fixed. No new pixels/colors are generated.
- After building shared contours, compare the single proposed output to an unchanged Facet baseline at the same resolution using the real 2x OpenCV-compatible raster. Pass only when changed pixels ≤0.15%, global RGB MAE ≤0.30 and max single-color mass difference ≤0.15%.
- Additional v21 protection: **white/nonwhite silhouette preservation** (zero changed), optional exact-color mass preservation, zero altered pixels inside designated protected rectangles (Kyoko left sleeve ROI x90..111, y263..289; Kyoko representative green RGB(149,211,27) mass fixed). All fall back to the baseline when a check fails.
- **No-vertex-gain gate**: a targeted pair that does not reduce total rendered vertices is rolled back even if its pixel deltas happen to be tolerable. Other v17/v18 modes are unaffected by this research-only rule.
- `targetedMergeStatus`, `targetedMergeMatched`, `targetedMergeChoice`, and raster rejection reasons allow failures to be verified rather than silently accepted.
- A failed trial returns the baseline regions and PNG exactly. No change to `main` or public frontend.

## Real Chrome 154, original 340x340 golden inputs

Chrome headless executed the actual `MinimalizerBrowserFallback.minimalizeFile` with subject guidance and the same budgets as the accepted Facet v15; each source was run with its Facet and Near baseline, followed by its own explicit pair trial. The existing `app.js requestBrowserFallback()` **Near** route was also checked against direct engine output (there is **no new public targeted UI route**).

| Source | Explicit directed pair | Result | Final regions | Facet→Final vertices | Actual changed PNG pixels |
| --- | --- | --- | ---: | ---: | ---: |
| Kyoko | donor 14 → recipient 17 | **PASS** | 39 | 1377 → **1366** | **3** |
| Kyoko | donor 18 → recipient 15 | **REJECT / no vertex gain** | 40 | 1377 → 1377 | **0** (exact rollback) |
| Kyoko | donor 18 → recipient 19 | **PASS** | 39 | 1377 → **1357** | **56** |
| Shirogane Noel | donor 16 → recipient 24 | **PASS** | 39 | 1232 → **1206** | **161** |
| Shirogane Noel | donor 34 → recipient 27 | **REJECT / rendered difference** | 40 | 1232 → 1232 | **0** (exact rollback; tentative change was 552px) |
| Ichijou Ririka | nonexistent donor 999 → recipient 998 (negative test) | **NOT FOUND** | 40 | 880 → 880 | **0** |

**Important:** these are five separately tested proposals. Kyoko donor 18 is shared by two competing proposals; they were **not** applied together. The count 39 represents one merge per experiment, not a validated globally applicable 37-region model.

Three individual trial merges produced a smaller polygon/vertex graph and each passed protected color, silhouette and real raster difference checks. Two failed candidates were automatically rolled back, and the Ririka invalid-ID control left the golden PNG unchanged. Kyoko representative green RGB(149,211,27) remains **1,994 px across the full output** (not a hand-segmented tie mask), and sleeve pixel (95,275) remains RGB(65,66,74).

## Interpretation and limitations

- This is the **first measured nonzero region-merge success** following v17/v18/v19's three zero-merge studies. It confirms targeted same-palette border elimination can be guarded by actual rendered fidelity and rolled back when unsafe.
- Accepted changes were **3, 56 and 161 pixels**, so final appearance is nearly unchanged. Fewer shape records/vertices **does not yet prove a visibly more intentional, straight geometric design**; the comparison montage shows most quality characteristics are shared with v15. Do not overpromise image aesthetics.
- The selected IDs are **specific to these three source images and this segmentation**. A production algorithm would need stable automatic candidate discovery, label-ID-independent ranking, protected feature ROIs, per-merge rollback and multi-source golden gates. Do not blindly hardcode these IDs into a user-facing quality mode.
- Current white/nonwhite silhouette check detects white-background transitions, not every semantic silhouette feature; additional visual contour tests are still needed before release.
- No comparison to official 3D references, no facial reconstruction, no training or GPU usage.

## Tests, evidence and decision

- New focused test `tests/test_browser_targeted_v21.py`: one explicit same-palette pair, orientation/ID rejection, invalid configuration fail-closed, complete pixel ownership, palette stability, protected tie-color/ROI/silhouette raster checks.
- Extended `v12/v13/v14/v15/v17/v18/v19/v20/v21` suite: **56 passed** in isolated Windows checkout; JS syntax check passed.
- GitHub Actions new workflow `.github/workflows/browser-single-pair-v21.yml` plus inherited workflows are checked on draft PR. Record confirmed conclusions, do not assume.
- Chrome benchmark `tools/run_browser_targeted_v21_chrome.py`, six-image report and diagnostics `tools/analyze_browser_targeted_v21.py`.
- [Google Drive v21 experiment evidence](https://drive.google.com/drive/folders/1gd5zjNFO6W92O5nR3J_LZHvHjhLmIiRO) under `chatGPT及びCodex用/Minimalizer`, including input images, six individual trial PNGs, golden baselines, comparison and amplified-change montages, JSON/CSV scores, and executable scripts. Save and verify files after this document.

**Ship gate: HOLD.** Three successful guarded one-pair experiments are research gains, not a complete visual-quality release. Next, v22 may rank and trial fresh candidates based on measured geometry without relying on per-image IDs, always enforcing per-candidate raster and color/silhouette constraints; then use multi-character golden visual review before considering a production deployment. If the artwork's overall visual geometry is still inadequate, pivot from merely reducing same-color internal partitions to restructuring major color planes.
