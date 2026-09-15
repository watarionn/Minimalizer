# Minimalizer 2.0 Calibration 04: Medium-detail Cleanup

Date: 2026-09-15
Base calibration: Calibration 03 (`6989b2741ea581dd307008142d872ae1eb60d60d`)
Branch: `feature/minimalizer-2-calibration-04-medium-detail`

## Goal

Reduce medium-size accessory and clothing color fragments that remain more detailed than the Approved Geometric Reference style.
Preserve the large face, hair, torso, arm, and outfit masses, and do not reopen Region Merge.
Geometry, contour topology, primitive fitting, and Palette Consolidation remain unchanged.

## Measurement

Calibration 02 already collapses unprotected Minimal regions with area ratio at most `0.0008` and importance at most `0.60`.
Calibration 04 measured the next retained band before selecting a threshold.

Three smoke cases showed that conservative safe collapses remain just above the micro-detail band.
The existing last-anchor, protected palette relationship, adjacency, coverage, and `target_min` guards were kept in every probe.

Area-limit probes on the canonical 18 cases produced:
- `0.0012`: mean groups `35.667`, 26 additional collapses, 2 cases at target minimum
- `0.0015`: mean groups `33.833`, 58 additional collapses, 3 cases at target minimum
- `0.0020`: mean groups `31.333`, 102 additional collapses, 6 cases at target minimum

`0.0015` was selected as the conservative medium-detail limit.
`0.0020` was rejected because the reduction accelerated too sharply across the corpus.
## Change

After the existing micro-detail cleanup, the Minimal preset may collapse a medium-detail style region when all of these are true:

- the shape remains a core coverage shape and is not hidden
- it is not protected and its current action is `RETAIN`
- area ratio is greater than `0.0008` and at most `0.0015`
- importance is at most `0.60`
- the fallback is an adjacent core region
- the last characteristic-anchor support is preserved
- every protected palette relationship remains valid
- the collapse reduces visual groups
- the result does not cross below the preset `target_min`

The medium-detail pass is enabled only for `minimal` by default.
Balanced, Detailed, and Ultra Minimal are unchanged.

## Canonical 18-case comparison

Calibration 03 versus Calibration 04 using the same direct pipeline and isolating the Detail Budget change:

- mean visual groups: `37.167 -> 33.833`
- visual-group range: `21..44 -> 21..43`
- additional style collapses: `58`
- cases with fewer visual groups: `15 / 18`
- cases at Minimal `target_min=28`: `3`
Smoke-case group changes:
- Kikirara-Vivi: `37 -> 31`
- Otonose-Kanade: `34 -> 28`
- Hakos-Baelz: `42 -> 41`

The canonical visual-regression run reported hard invariant failures `0 / 18`.

## Regression status

- Detail Budget tests: `13 passed`
- V2 regression: `106 passed`
- Full repository regression: `438 passed, 2 failed, 1 warning`

The two full-suite failures are unchanged from Calibration 03 and are caused by the missing asset `tests/assets/false_face_phase85.png`.
They are not attributed to Calibration 04.

## Decision

Accept `medium_detail_area_ratio = 0.0015` and `medium_detail_importance_limit = 0.60` for the Minimal preset.
Calibration 04 stays entirely in the late Detail Budget stage and does not modify Region Merge, hierarchy cuts, contours, primitives, or palette construction.
