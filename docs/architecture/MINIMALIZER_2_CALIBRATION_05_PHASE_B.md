# Minimalizer 2.0 Calibration 05 Phase B

Updated: 2026-09-15
Status: engineering candidate validated
Branch: `feature/minimalizer-2-calibration-05-planar-polygonization`

## Goal

Phase B implements conservative Shared-Boundary Line Fitting for the Minimal preset.
It follows Phase A, which showed that increasing global RDP epsilon did not materially improve long-line support.

The 18 approved geometric references are used as comparison material, not as per-image special cases.
Region Merge and Detail Budget target policies remain unchanged.

## Root cause found

The shared BoundaryGraph was splitting nearly every pixel-scale turn as a `strong_structural_corner`.
On the five smoke cases, protected split vertices were dominated by that reason:
- Kikirara-Vivi: `2432 / 2571`
- Otonose-Kanade: `1909 / 2038`
- Todoroki-Hajime: `1130 / 1260`
- Raora-Panthera: `2861 / 2996`
- Hakos-Baelz: `2757 / 2885`

This fragmented visible boundaries into thousands of short chains before line fitting could act.

## Production behavior

For the Minimal preset only:
- pixel-scale strong corners are no longer mandatory chain split points
- multi-region junctions, image borders/corners, and existing protected boundary reasons remain hard structure
- a line-fitting candidate may replace a locally noisy span by its chord
- endpoints stay fixed on the shared BoundaryGraph, so both neighboring regions receive the same edge
- every candidate still passes the existing intersection, topology, IoU, centroid, area, and directional-loss guards

Conservative default gates:
- minimum points: `4`
- minimum span: `0.03 * image diagonal`
- maximum perpendicular deviation: `0.004 * image diagonal`
- minimum chord/arc efficiency: `0.94`
- enabled preset: `minimal`

The stronger probe (`0.006`, efficiency `0.92`) improved support further but consumed too much guard margin, so it was rejected as the default.

## 18-case result

Comparison baseline is the Phase A / Calibration 04 behavior rendered with the same diagnostic.
- hard invariant failures: `0 / 18`
- mean long-line support: `0.195941 -> 0.235422` (`+20.15%`)
- cases with improved long-line support: `15 / 18`
- mean current/reference support ratio: `0.289346 -> 0.346412`
- mean contour vertices: `5696.72 -> 1427.11` (`-74.95%`)
- minimum Contour IoU: `0.919192 -> 0.900000`
- maximum directional loss: `0.122656 -> 0.134615`
- mean visual groups: `34.556 -> 34.667`

Only Gigi-Murin and Hakos-Baelz gained one visual group; the other 16 cases retained their prior group count.
Todoroki-Hajime stayed at `21` visual groups, so Phase B did not solve geometry by further flattening style.

Three cases did not improve the raster Hough support score:
- Gigi-Murin
- Hakos-Baelz
- Otonose-Kanade

Those cases remain guard material for the next phase. The metric is diagnostic, not a single-objective optimizer.

## Visual review

The all-18 comparison sheet shows a real but intentionally conservative improvement: stair-step boundaries become longer and more deliberate without changing the overall color-group strategy.
The approved references are still substantially more faceted and macro-geometric than current output.

The remaining gap is no longer best described as raw boundary noise alone. Current output still follows many source-image region decisions, whereas approved references combine those decisions into intentional large planar facets.
This suggests that the next investigation should focus on macro planar-facet reconstruction / effective visual-group geometry rather than stronger line fitting.

Do not interpret this as permission for blanket face or accessory deletion. Hakos-Baelz and Raora-Panthera remain explicit structure-preservation guards.

## Regression

Focused contour/regression tests: `20 passed`.
V2 regression: `110 passed`.
Full repository: `442 passed, 2 failed, 1 warning`.
The two failures are the known missing `tests/assets/false_face_phase85.png` failures and are unrelated to Phase B.

## Decision

Phase B conservative Shared-Boundary Line Fitting is accepted as the engineering direction for Calibration 05.
It does not reopen Region Merge and does not change Detail Budget target policies.
The stronger line-fit candidate is rejected for now because the conservative candidate provides meaningful support gain with better guard margin.

Recommended next engineering step: investigate Phase C macro planar-facet reconstruction using the same 18-case comparison material, beginning with a diagnostic/probe rather than another global simplification knob.
