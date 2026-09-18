# Minimalizer 2.0 Calibration 06 Phase C

Updated: 2026-09-17
Status: PASS locally
Scope: rembg foreground confidence calibration

## Goal

Phase B proved that `isnet-anime` provides strong character foreground masks, but the initial linear confidence mapping made the existing subject/background hard barrier fire too broadly.
Phase C keeps the accepted rembg model and the existing Region Merge contract, and calibrates only provider confidence so ambiguous evidence cannot become hard structure too easily.

No Region Merge thresholds, weights, SLIC targets, visual thresholds, facet rules, or preset semantics are changed.
The rembg mask remains analysis guidance only and is never rendered as final geometry.

## Confidence calibration

Phase B used:
`confidence = clip(2 * abs(p - 0.5), 0, 1)`

Phase C uses:
`confidence = clip(2 * abs(p - 0.5), 0, 1) ** 2`

This changes representative certainty from `p=0.90 -> 0.80` to `0.64`, while `p=0.95` remains strong enough at `0.81` to cross the existing Region Merge confidence gate when region-level evidence is also sufficiently pure.
## Approved-18 result

The calibrated `isnet-anime` guidance was run through the same hosted `analysis_max_side=400` Minimal pipeline for all 18 approved cases.

- algorithm digest changed: `18 / 18`
- hard invariant failures: `0 / 18`
- mean final Region Merge root delta: `+4.167`
- mean visual-group delta: `+1.278`
- mean `subject_background` barrier delta: `+959.833`

Compared with the Phase B linear mapping, mean final-root growth falls from `+5.667` to `+4.167` while retaining about `91.5%` of the subject/background barrier activity.
On the exact same eight-case visual subset used in Phase B, mean visual-group delta falls from `+4.000` to `+1.625`.

The largest Phase C group increases are Vestia-Zeta `+6`, Koseki-Bijou `+4`, Momosuzu-Nene `+4`, Isaki-Riona `+3`, and Kikirara-Vivi `+3`.
Visual review showed that Vestia's increase corresponds to clearer face/hair/foreground-arm separation rather than obvious micro-fragmentation.
Raora-Panthera moves in the desired simplifying direction from `37 -> 34` visual groups.

## Implementation

`RembgGuidanceConfig` now exposes `confidence_power` with a conservative default of `2.0`.
Values below `1.0`, non-finite powers, and empty model names are rejected.
The reusable comparison tool accepts `--confidence-power` so the calibration remains reproducible without modifying Region Merge configuration.
## Validation

Adapter + analysis-guidance tests: `11 passed`.
V2-focused repository regression: `183 passed, 334 deselected, 1 warning`.
Approved-18 guided comparison: hard invariant failures `0 / 18`.
Machine-readable evidence: `MINIMALIZER_2_CALIBRATION_06_PHASE_C_EVALUATION.json`.

The base Minimalizer requirements remain unchanged. rembg evaluation/runtime dependencies remain isolated in Python 3.11.
No GitHub Actions run was started.

## Decision

Accept `confidence_power=2.0` as the current rembg foreground-guidance calibration.
Keep `isnet-anime` as the preferred character/illustration foreground model.
The foreground contract is now stable enough to proceed to semantic hints.

MediaPipe is the next provider to evaluate for hair / face-skin / clothes / body semantic guidance.
Its masks must feed `SemanticGuide` and existing Region Merge / Primitive hints only. They must not become final rendered geometry.
Grounded-SAM remains deferred unless MediaPipe leaves a demonstrated semantic-part gap; YOLO segmentation remains later still.

Do not create/update a PR, touch `main`, merge, deploy, or intentionally run GitHub Actions without the corresponding explicit approval.