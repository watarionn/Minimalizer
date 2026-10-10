# MinimalizerPublic R25: original-source, Stage04, Stage8 and Chrome error attribution

**2026-10-10 | R25 research engineering PASS, actual source-photo fidelity remains HOLD, production NO-GO.**

R25 research is stacked on the R22–R24 Draft PR #377. It changes **only** the private evidence generator `scripts/verify_public_r25_source_owner_attribution.py`, its test file `tests/test_public_r25_source_owner_attribution.py`, and this report. No source photo, original Stage04 mask, original Stage8 geometry, palette, live Public route, Local Minimalizer/Worker, GitHub main or deployed hosting was modified. No generated/invented pixels or eye/mouth features were introduced.

## Real authority, not inferred from color alone

For both signed original cases, R25 pins exact SHA-256 of the original 340×340 RGBA photo, authentic 11-owner SA10.34 Stage8 JSON, historical SA10.41 complete SVG, frozen OpenCV full-scene reference RGB and signed Stage04 face/left/right arm masks. It replays the actual full-character source SVG in headless **Chrome 154.0.8037.98** at 340px and independently checks the original SA10.41 count (GC001 3,919; Raden 2,681 Chrome vs frozen OpenCV differing pixels).

Three **different quantities must never be conflated**:

1. Source-photo RGB vs frozen OpenCV reference within an authentic owner-mask region: upstream approximation/color mismatch. Not proof of anatomy/semantic truth.
2. Actual Chrome RGB vs the same frozen OpenCV reference: raster/SVG browser discrepancy. This can arise from contour boundaries, fill rules and micro-rings; not necessarily a wrong body part.
3. Signed historical Phase04 binary mask vs signed source-derived Stage8 owner raster XOR, plus the exact-source-border-connected RGB mask overlap: provenance/binding discrepancy and **conservative background contamination witness**, not an anatomical segmenter.

For each of **all 11** signed Stage8 owner masks, R25 computes source/reference RGB MAE, Chrome/reference wrong pixels, masked exact RGB background overlap, and subdivides attribution into a two-pixel-eroded owner **interior** and its exact complement **boundary band**. For the three independently signed Stage04 face, left arm, right arm masks, it also calculates Stage8 mask miss/extra/XOR. These per-owner regions overlap and are **not mutually exclusive**: summing their wrong-pixel counts would double-count rendered pixels.

## Genuine two-original-source findings

| Diagnostic | GC001 | Raden |
|---|---:|---:|
| Full Chrome/reference wrong pixels | 3,919 | 2,681 |
| Signed face mask pixels | 4,937 | 4,052 |
| Face Chrome wrong, boundary/interior | **140 / 0** | **122 / 0** |
| Signed left-arm mask pixels | 2,715 | 10,419 |
| Left arm Chrome wrong, boundary/interior | **206 / 0** | **237 / 0** |
| Signed right-arm mask pixels | 6,486 | 9,870 |
| Right arm Chrome wrong, boundary/interior | **185 / 14** | **154 / 101** |
| Signed left-arm source/reference RGB MAE | **76.071332** | **23.351185** |
| Signed right-arm source/reference RGB MAE | **55.439562** | **25.660014** |
| Right arm source exact-border RGB overlap | **533** | **3** |
| Left arm source exact-border RGB overlap | **0** | **7** |
| Stage8/signed Phase04 left-arm mask XOR | **5** (1 missed, 4 extra) | **0** |
| Stage8/signed Phase04 right-arm mask XOR | **24** (0 missed, 24 extra) | **2** (0 missed, 2 extra) |

GC001's signed right-arm boundary shows a substantial **exact source-background-connected color** risk already at Phase04. Previous C02 history research additionally observes 648 such pixels in Phase03 and an independent historical-left-arm mask change of 385 pixels; R25 does **not** reassign a definitive causal origin to Phase03, nor overwrite historical masks. Raden's small right-arm overlap is a valuable independent control that prevents incorrectly generalizing the GC001 risk.

In the frozen Chrome/reference comparison, protected **face and left arm discrepancies lie entirely inside the boundary band** for both images, while right-arm interior disagreement persists (GC001 14 pixels, Raden 101). The face source/reference RGB difference is expected to include genuine source details omitted by formal face-hidden Minimalizer policy. **Do not draw eyes, nose or mouth to reduce an MAE metric.**

The 11-owner mask metrics separately expose prominent Chrome/reference discrepancy inside **head, hair, major clothing**. GC001 owner-mask Chrome changed pixels: head 1,264; hair 1,032; major clothing 651. Raden hair 847, head 684, major clothing 503. These masks overlap, so numbers are diagnostics, not parts summing to the whole. Internal garment and arm source colors require independent signed semantic review before any recolor/painting.

## Outcome and next action

**R25 engineering work is complete**: signed two-case authority revalidated, genuine Chrome 340px rerender replayed, 11-owner source/color and rendered-error attribution plus signed Phase04 mask lineage measured, immutable private contact sheets generated. No repair is automatically accepted. The original Stage8 cost **GC001 3,604 versus 1,887; Raden 2,370 versus 1,412 remains FAIL**. Two source originals are not Approved18/78. C02 independent source-only semantic model evidence and C04 human Golden remain HOLD. Likewise Chrome/resvg whole-scene DPR2, real iPhone Safari, MPL and real host rollback are unapproved.

Tests: **155/155 Public R1–R25 and Local/Public isolation tests PASS**, including 11 R25 tests covering independent source-vs-renderer partitions, synthetic boundary/interior split, rejected unsigned source, nonbinary masks, no output overwrite and non-promoting operation. Two independent actual Chrome runs yield **3/3 byte-identical evidence outputs**:
- `GC001_r25_PRIVATE_owner_chrome_error_board.png` SHA-256 `2da8e7b24da5e724d3082c0e25f25b1edfad5b8ad7bf42b93e67f678d60e6374`
- `Raden_r25_PRIVATE_owner_chrome_error_board.png` SHA-256 `aef3f122ca01e822094962f17a6f62df6cc9eb4214eec09503f51089bb711c3e`
- `public_r25_owner_source_rgb_error_attribution.json` SHA-256 `5f7bb72c101c3254a8e2f9beb0c60063d2bb484518dcced12f96726fcd8bd9aa`

Store private original-photo contact sheets, private full numeric evidence and SHA manifest **only** under `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R25_20261010`; public GitHub includes source-free algorithm/tests/coordinate-free report only.

**R26 target:** use this complete provenance/ROI attribution to develop a verified *source-only, independently approved* correction for Phase03/04 owner bindings, then test full composition and per-owner Chrome 340/DPR2 without changing signed originals or face-hidden policy. Prioritize GC001 right arm background leak and Raden right arm interior 101-pixel renderer discrepancy; separately address clothing tie/staff semantics. No automatic product merge based on numerical MAE alone.
