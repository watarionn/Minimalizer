# Minimalizer 2.0 Calibration 05 Phase A

Updated: 2026-09-15
Status: completed diagnostic phase
Branch: `feature/minimalizer-2-calibration-05-planar-polygonization`

## Goal

Calibration 05 targets Planar Polygonization / Long-Line Reconstruction.
Phase A adds an observational diagnostic before changing production geometry.
The diagnostic measures the rendered scene after Detail Budget and Primitive Fitting.

New regression metrics:
- `visible_edge_density`
- `long_line_support`
- `long_line_count`

`long_line_support` is the fraction of Canny edge pixels supported by sufficiently long Hough line segments.
The minimum line length and allowed gap scale with image diagonal, so the metric is resolution-aware.
The default diagnostic parameters are:
- minimum line length: `0.04 * image diagonal`
- maximum line gap: `0.007 * image diagonal`
- Hough threshold: `25`

The diagnostic is observational only and does not change `algorithm_digest`.
## Five-case reference baseline

Smoke cases:
- Kikirara-Vivi
- Otonose-Kanade
- Todoroki-Hajime
- Raora-Panthera
- Hakos-Baelz

Approved References were resized to each current output size before comparison.
Current/reference `long_line_support` ratios:
- Kikirara-Vivi: `0.1525`
- Otonose-Kanade: `0.2965`
- Todoroki-Hajime: `0.2831`
- Raora-Panthera: `0.2911`
- Hakos-Baelz: `0.3009`

Mean ratio: `0.2648`.
All five smoke runs had invariant failures `0`.

Stage decomposition showed Detail Budget is not the primary loss point.
Primitive/Final support was comparable to or better than Palette support in four of five smoke cases.
The dominant limitation is therefore upstream shared-boundary geometry, not another global Detail Budget collapse.
## Conservative epsilon probe

Only `minimal_epsilon_ratio` was varied. Region Merge, palette, Detail Budget, and all safety guards stayed unchanged.

| epsilon | mean long-line support | mean contour vertices | min Contour IoU | max directional loss | invariant failures |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.022 | 0.162654 | 5236.4 | 0.934010 | 0.063979 | 0 |
| 0.024 | 0.141739 | 5227.6 | 0.931011 | 0.063979 | 0 |
| 0.026 | 0.163836 | 5216.0 | 0.930120 | 0.063979 | 0 |
| 0.030 | 0.166273 | 5196.6 | 0.912322 | 0.063979 | 0 |

Increasing global RDP strength does not materially improve long-line support.
At `0.030`, support improves only about 2.2% relative to baseline while worst Contour IoU drops substantially.
Therefore a stronger global epsilon is rejected for Calibration 05.

## Regression

V2 regression: `107 passed`.
Full repository: `439 passed, 2 failed, 1 warning`.
The two failures are the existing missing-asset failures for `tests/assets/false_face_phase85.png`.
No new regression failure was introduced.
## Decision

Calibration 05 Phase B should implement an explicit shared-boundary line-fitting candidate rather than increasing global contour epsilon.
The candidate must operate on the shared BoundaryGraph so both neighboring regions receive the same reconstructed edge.
It should target locally noisy runs that can be represented by a longer straight segment while preserving protected vertices and chain endpoints.

Acceptance gates for Phase B:
- hard invariant failures remain `0`
- Contour IoU and directional guards remain inside existing limits
- shared-boundary agreement remains exact
- no new coverage holes or palette/anchor regressions
- smoke-case `long_line_support` improves meaningfully, not merely vertex count
- Todoroki-Hajime must not become flatter through additional style collapse
- Raora-Panthera accessory planes must remain distinct

Do not reopen Region Merge in Phase B.
Do not change Detail Budget targets in Phase B.
