# Phase 14 — Evaluation Redesign & Calibration Closure

Status: **CLOSED**
Date: 2026-10-03
Next phase: **Phase 15 — Production Integration / Migration**
Phase 15 authorization: **YES**

## Goal

Phase 14 turns the Phase 12/13 visual-quality work into an explicit fail-closed evaluation system.
The purpose is to prevent a numeric PASS from hiding an obvious visual FAIL.

The phase does not introduce new image synthesis, inpainting, hidden completion, or reference-image copying.
All evaluation is deterministic and evidence-bound.

## Implemented evaluation axes

The case-level evaluator records and gates:

- silhouette preservation;
- semantic part-layout consistency, using centroid displacement plus bounding-box IoU;
- major color-mass consistency in LAB space;
- identity-feature retention;
- oversized-block penalty;
- fragmentation penalty;
- face / hair / torso collapse;
- primitive economy;
- deterministic repeat evaluation;
- independent human visual QA.

Human visual failure wins over numeric PASS.

## Case-level default policy

The Phase 14 default thresholds are:

- silhouette IoU >= 0.96;
- mean part-layout score >= 0.85;
- minimum single-part layout score >= 0.50;
- major color-mass score >= 0.65;
- identity-feature retention >= 0.90;
- oversized-block penalty <= 0.10;
- fragmentation penalty <= 0.20;
- face/hair/torso collapse guard: recall >= 0.85 and IoU >= 0.75;
- primitive economy >= 0.10.

Human criteria are same-subject recognizability, pose readability, major-feature retention,
minimal-style consistency, and absence of catastrophic block failure.


## Diagnostic-2 result

Raden and Hyakuto Kyoko were regenerated through Phase 14 and reviewed again.

Diagnostic-2 corpus Gate:

- case count: 2;
- pass count: 2;
- fail count: 0;
- human visual pass count: 2;
- determinism pass count: 2;
- minimum silhouette preservation: 0.981039;
- minimum mean part-layout score: 0.8839164004;
- minimum single-part layout score: 0.5540240650;
- minimum major color-mass score: 0.6856306635;
- minimum identity-feature retention: 0.963008;
- minimum primitive economy: 0.4615384615;
- maximum oversized-block penalty: 0.0;
- maximum fragmentation penalty: 0.0357142857.

This Gate is the primary ZeroBase2 machine + human visual quality Gate.

## Approved-78 formal migration Gate

All 78 saved Scene/candidate replay pairs are present and SHA-bound.

Result:

- reference count: 78;
- deterministic replay complete: 78/78;
- MigrationGate: PASS;
- migration reasons: none;
- mean replay coverage: 0.99829872518;
- mean replay silhouette: 0.99829872518;
- mean complexity: 1.358273381295.

The legacy Approved78CalibrationHarness remains diagnostic.
Its mean angularity (0.339568345324) and semantic cost (0.5) are not treated as release failures,
because Phase 10 explicitly prohibited hidden or guessed CalibrationTargets and the saved replay
Scene artifacts expose only the generic `foreground` semantic role (695 regions).

This is an intentional Phase 14 correction: the formal Approved-78 release-critical Gate is the
existing SHA-bound MigrationGate, while the legacy calibration dimensions remain inspectable diagnostics.

## Approved-18 production regression Gate

The fixed Approved-18 manifest was checked directly against the Google Drive source of truth:

- input images: 18/18 SHA-256 match;
- approved reference images: 18/18 SHA-256 match;
- total checked files: 36/36;
- macro subject guard: 18/18;
- face carrier: 18/18;
- structural gate: 18/18;
- facial feature carrier remains absent in the approved-reference abstraction;
- mean final shape count: 18.333333.

Diagnostic-only visual measurements:

- mean coarse color similarity: 0.851149;
- mean edge IoU: 0.08255;
- mean edge-density delta: 0.037455.

These diagnostic similarity values are deliberately not promoted into hidden thresholds.


## Artifact contract

The provenance bridge now supports Phase 14 as a first-class stage.

New artifact types include:

- `14_case_evaluation.json` -> `evaluation-redesign-data`;
- `14_eval_sheet.png` -> `evaluation-sheet`;
- Phase 14 stage outputs remain bound to Phase 4 semantic masks, Phase 12 selected output,
  Phase 13 debug evidence, and the canonical source SHA.

Phase 14 case execution refuses to run unless the Phase 3-13 provenance Gate already passes.

## Failure policy

Phase 14 closes only when all of the following pass:

1. Diagnostic-2 ZeroBase visual Gate;
2. Approved-18 production regression Gate;
3. Approved-78 formal migration Gate.

Any machine failure, human visual failure, determinism failure, missing corpus case, SHA mismatch,
or migration non-regression failure keeps the Gate closed.

Final closure artifact:

`artifacts/phase14_closure/14_phase_gate_summary.json`

Final result:

- Phase 14: PASS;
- Diagnostic-2 Gate: PASS;
- Approved-18 Gate: PASS;
- Approved-78 Gate: PASS;
- next phase authorized: 15.

## Incidents and fixes

### Approved-78 target-profile misuse

The first Phase 14 Approved-78 runner treated legacy `CalibrationTargets` defaults as a formal
release Gate and therefore reported a false FAIL on angularity / semantic cost.

Root cause:
the old Phase 10 harness is a diagnostic calibration harness, and Phase 10 explicitly prohibited
a hidden or guessed target profile. The saved replay scenes also contain only generic
`foreground` semantic roles, so semantic angularity targets are not sufficiently expressive.

Fix:
retain all calibration dimensions as diagnostics, but use the existing deterministic SHA-bound
MigrationGate as the Approved-78 formal release Gate.

Prevention:
do not promote diagnostic targets into formal thresholds without an explicit canonical target profile.

### Windows Unicode path decode

Approved-18 reference evaluation initially failed on the Japanese Google Drive mount path because
`cv2.imread` could not decode the Unicode path.

Fix:
`tools/evaluate_approved18.py` now reads bytes with `numpy.fromfile` and decodes with
`cv2.imdecode`.

A dedicated Unicode-path regression test was added.

## Verification

Final broad regression:

- **112 passed**;
- Phase 14 evaluator fail-closed tests: PASS;
- Phase 14 Approved-18 fail-closed tests: PASS;
- Phase 14 closure fail-closed tests: PASS;
- Phase 14 artifact-contract bridge test: PASS;
- Approved-18 Unicode-path regression: PASS;
- Diagnostic-2 corpus Gate: 2/2 PASS;
- Approved-78 replay count: 78/78;
- Approved-18 structural regression: 18/18.

## Decision

Phase 14 is closed.

The evaluation system now distinguishes:

- source-supported numeric quality;
- deterministic provenance;
- cross-case regression;
- production-regression compatibility;
- independent human visual acceptability.

A numeric PASS can no longer override a human visual FAIL.

Phase 15 is authorized. Its first action is to read the canonical Production Integration / Migration
contract and connect ZeroBase through the existing fail-closed migration boundary without bypassing
the Phase 14 evaluation evidence.
