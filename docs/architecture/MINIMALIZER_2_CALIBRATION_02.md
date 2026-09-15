# Minimalizer 2.0 Calibration 02: Micro-detail Cleanup

Date: 2026-09-15
Base calibration commit: `9f357e54f22f9f3be9a2194375b420e6df1f81c6`
Branch: `feature/minimalizer-2-calibration-02-micro-detail`

## Goal

Reduce tiny isolated color/style fragments after Calibration 01 without changing Region Merge, Hierarchy Cut, Contour geometry, Primitive fitting, or Palette Consolidation.
Geometry coverage must remain unchanged.

## Investigation

The three smoke cases had no semantic tags in the V2 contour results, so facial/accessory over-detail was not caused by `critical_semantic` protection.
The remaining fragments survived because Detail Budget stopped as soon as the visual-group upper bound was satisfied.

Manifest verification confirmed all 18 source files still match the SHA-256 values in `tests/assets/approved18_manifest.json`.
A detached-worktree reproducibility audit also confirmed that commit `9f357e5` itself produces deterministic results; earlier transient Calibration 01 measurements were corrected in the Calibration 01 document.

## Change

After the normal Detail Budget pass, the Minimal preset may perform a micro-detail style collapse when all of these are true:

- the shape is a core coverage shape and remains geometrically present
- it is not protected
- current action is `RETAIN`
- area ratio is at most `0.0008`
- importance is at most `0.60`
- the fallback is an adjacent core shape
- the last characteristic-anchor support is preserved
- every protected palette relationship remains valid
- the collapse reduces visual groups
- the result does not cross below the preset `target_min`

The default micro-detail presets are `("minimal",)` only. Balanced, Detailed, and Ultra Minimal are unchanged in this calibration.

## Smoke review

Using the canonical source images:

- Kikirara-Vivi: `40 -> 37` groups, 3 additional micro collapses
- Otonose-Kanade: `44 -> 34`, 10 additional micro collapses
- Hakos-Baelz: `44 -> 42`, 2 additional micro collapses

The visible changes remove tiny color islands while retaining the head/hair/torso/arm/outfit masses and all geometry.
An area threshold of `0.0012` or higher was rejected as too aggressive for the first micro-detail calibration.

## Canonical 18-case result

Compared with committed Calibration 01 (`9f357e5`):

- cases: `18 / 18`
- hard invariant failures: `0`
- budget overflow cases: `0`
- visual-group range: `21..44`
- mean visual groups: `41.944 -> 37.167`
- total style collapses: `112 -> 198`
- additional micro-detail collapses: `86`
- cases whose group count decreased further: `14 / 18`
- cases reaching the `target_min` of 28: `2`
- minimum contour IoU: `0.9191919192` (unchanged)
- mean contour IoU: `0.941356` (unchanged)

The canonical Closure commit (`2499b3a`) re-run measured mean visual groups `48.278`, so the progression is:

`48.278 (Closure) -> 41.944 (Calibration 01) -> 37.167 (Calibration 02)`

## Determinism audit

Kikirara-Vivi was run three times in one Python process and five times in separate Python processes.
All runs produced the same algorithm digest, contour IoU, visual-group count, and selected-region count.

Digest during the Calibration 02 audit:
`169afa5d70b2329dd402d26d736715396f692443c464349c9321d9c65e47efff`

## Decision

Calibration 02 is accepted if the V2 and full-repository regressions remain clean apart from the pre-existing missing `false_face_phase85.png` asset failures.
The next calibration should focus on visible contour jaggedness or larger accessory simplification, without lowering the established structural/coverage gates.
