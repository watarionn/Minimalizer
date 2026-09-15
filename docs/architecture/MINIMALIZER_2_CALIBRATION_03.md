# Minimalizer 2.0 Calibration 03: Weak-corner Cleanup

Date: 2026-09-15
Base calibration commit: `e05dafdca122d2fe622bd28ccf69b01936f53e40`
Branch: `feature/minimalizer-2-calibration-03-contour-micro-cleanup`

## Goal

Reduce weak local zigzags without globally increasing contour epsilon.
Keep shared-boundary consistency, region topology, IoU, directional guards, and Calibration 02 detail-budget behavior unchanged.

## Investigation

A global Minimal epsilon increase had poor cost/benefit in Calibration 01.
Calibration 03 instead adjusts which turning points are pinned as `strong_structural_corner` split vertices.

The baseline strong-corner threshold is `0.65`.
Threshold probes were run at `0.6525`, `0.655`, `0.6575`, `0.66`, `0.67`, and `0.68`.
Values from `0.655` upward began changing directional loss or contour IoU on some smoke cases.
`0.6525` reduced vertices while leaving those metrics unchanged in the probe set.

## Change

Only the Minimal preset uses `minimal_strong_corner_threshold = 0.6525`.
Detailed, Balanced, and Ultra Minimal continue to use `0.65`.

The higher threshold means a very weak turn is less likely to split a shared boundary into separately protected chains. Existing RDP simplification and all topology/quality guards still decide whether the resulting chain simplification is accepted.

## Canonical 18-case comparison

Calibration 02 (`0.65`) versus Calibration 03 (`0.6525`):

- cases: `18 / 18`
- hard invariant failures: `0`
- base simplified vertices: `102508`
- calibrated simplified vertices: `102291`
- removed vertices: `217` (`0.212%`)
- cases with fewer vertices: `18 / 18`
- cases with changed minimum contour IoU: `0 / 18`
- cases with changed maximum directional loss: `0 / 18`
- visual-group range: `21..44` (unchanged)

Largest reductions included Kikirara-Vivi `5862 -> 5824`, Momosuzu-Nene `6316 -> 6288`, Hakos-Baelz `6298 -> 6276`, and Mori-Calliope `6597 -> 6576`.

## Rejected stronger calibration

`0.655` and above were not adopted. At stronger thresholds, Hakos-Baelz directional loss changed, and still higher values caused measurable contour-IoU loss on Kobo-Kanaeru, Houshou-Marine, and other cases.

## Decision

Accept `0.6525` as the conservative weak-corner calibration if automated regressions remain clean apart from the known missing `false_face_phase85.png` asset failures.
