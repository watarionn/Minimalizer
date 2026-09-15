# Minimalizer 2.0 Calibration 01: Coarseness

Date: 2026-09-15
Base closure commit: `2499b3a09f61fbbe1ee2ad049473b8d552cdb00c`
Branch: `feature/minimalizer-2-calibration-01-coarseness`

## Goal

Reduce excess small visual planes while preserving the Phase X structural and coverage gates.
Do not reopen Region Merge architecture for this calibration.

## Change

Only the Minimal preset Detail Budget defaults are changed:

- visual-group target: `35..60` -> `28..44`
- collapse importance limit: `0.56` -> `0.60`

Contour epsilon remains `0.022`.
A probe at `0.026` reduced very few vertices while lowering contour IoU on Kikirara-Vivi, so contour calibration was rejected for this step.

## Smoke probe

With the new target:

- Kikirara-Vivi: `40 -> 40` visual groups, no forced collapse
- Otonose-Kanade: `60 -> 44`, 16 style collapses
- Hakos-Baelz: `55 -> 44`, 11 style collapses

All three retained zero hard-invariant failures.

## Canonical 18-case result

- cases: `18 / 18`
- hard invariant failures: `0`
- budget overflow cases: `0`
- visual-group range: `21..44` (closure baseline was `21..60`)
- mean visual groups: `41.944` (closure baseline: `48.278`)
- total style collapses: `112`
- cases with at least one collapse: `13 / 18`
- minimum contour IoU: `0.9191919192` (unchanged from closure)

The calibration reduces style fragmentation without removing core geometry or weakening contour guards.

Calibration 02 later re-ran commits `2499b3a` and `9f357e5` in detached worktrees against manifest-verified inputs. The values above are the canonical commit-to-commit measurements; earlier transient probe values were corrected by that audit.

## Decision

Calibration 01 is accepted if repository regression remains clean apart from the pre-existing missing `false_face_phase85.png` asset failures.
The next calibration should address visible jaggedness or facial/accessory over-detail without undoing this coarseness gain.
