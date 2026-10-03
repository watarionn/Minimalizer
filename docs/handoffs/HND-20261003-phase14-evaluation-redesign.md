# HND-20261003 Phase 14 Evaluation Redesign & Calibration

## Status

**CLOSED / Phase 15 entry authorized**

Phase 14 was implemented as an evaluation-only redesign. No Phase 14 rendering exception was added.

Closure artifact:

- `artifacts/phase14_closure/14_phase_gate_summary.json`
- `pass=true`
- `next_phase_authorized=15`

## Why Phase 14 existed

The 1st-cycle numeric gates could report PASS while Raden/Kyoko still failed visual review.
Phase 14 therefore separates machine metrics, deterministic replay, historical regression gates, and human visual QA.

A numeric PASS never overrides a human visual FAIL.

## Implemented evaluation axes

Case-level Phase 14 evaluation now records:

- silhouette preservation
- part layout consistency
  - centroid displacement
  - bounding-box IoU
  - corpus mean and per-part minimum
- major color mass consistency in LAB space
- identity-feature retention
- oversized-block penalty
- fragmentation penalty
- face/hair/torso collapse guard
- primitive economy
- determinism
- human visual QA

Human criteria:

- same-subject recognizability
- pose readability
- major-feature retention
- minimal-style consistency
- catastrophic-block-failure absence

## New implementation

### Core

- `minimalizer_zerobase/evaluation/phase14.py`
  - `Phase14EvaluationPolicy`
  - `evaluate_phase14_case`
  - `render_phase14_eval_sheet`
  - `write_phase14_artifacts`
  - corpus summary builders

### Runners

- `tools/run_zerobase_phase14.py`
- `tools/run_zerobase_phase14_corpus.py`
- `tools/run_zerobase_phase14_approved18.py`
- `tools/run_zerobase_phase14_approved78.py`
- `tools/run_zerobase_phase14_closure.py`

### Artifact contract

`minimalizer_zerobase/artifact_contract/bridge.py` now supports Phase 14.

New Phase 14 artifact types:

- `14_case_evaluation.json` -> `evaluation-redesign-data`
- `14_eval_sheet.png` -> `evaluation-sheet`
- `14_corpus_summary.json` -> `evaluation-corpus-summary`

Canonical Phase 14 case output:

- `14_case_evaluation.json`
- `14_eval_sheet.png`
- `preview.png`
- `metrics.json`
- `stage.json`

## Diagnostic-2 Gate

Cases:

1. Juufuutei-Raden
2. Hyakuto-Kyoko

Latest corpus result:

- case count: 2
- pass count: 2
- human visual pass count: 2
- determinism pass count: 2
- fail count: 0

Minimum corpus scores:

- silhouette preservation: 0.981039
- identity retention: 0.963008
- major color mass consistency: 0.685631
- part-layout mean: 0.883916
- part-layout minimum: 0.554024
- primitive economy: 0.461538

Maximum penalties:

- oversized-block penalty: 0.0
- fragmentation penalty: 0.035714

Raden Phase 14 provenance:

- PASS / 86 artifacts

Kyoko Phase 14 provenance:

- PASS / 86 artifacts

## Approved-18 regression

Canonical manifest:

- `tests/assets/approved18_manifest.json`

Input and Approved-reference files were reacquired from Google Drive canonical sources.

Hash verification:

- input SHA-256: 18/18
- Approved-reference SHA-256: 18/18

Existing canonical evaluator:

- `tools/evaluate_approved18.py`

Result:

- structural gate: 18/18 PASS
- macro guard: 18/18
- face carrier: 18/18
- mean shape count: 18.333333
- mean coarse color similarity: 0.851149
- mean edge IoU: 0.08255
- mean edge density delta: 0.037455

Formal Phase 14 regression result:

- `artifacts/phase14_approved18/14_approved18_regression_gate.json`
- PASS

Important interpretation:

Approved-18 is the existing production `approved_reference` regression Gate.
The generated images still differ visually from the Approved references in several cases.
Therefore this Gate proves that the historical production regression contract has not broken; it is **not** evidence of exact visual equivalence and does not replace Diagnostic-2 human visual QA.

Three review boards were also generated under:

- `artifacts/phase14_approved18_review/`

## Approved-78 formal Gate

Saved replay corpus:

- 78/78 Scene artifacts
- 78/78 candidate artifacts

Existing Migration evidence:

- all source SHA-256 verified
- all Approved-reference SHA-256 verified
- all replay deterministic

Formal result:

- replay complete: true
- MigrationGate: PASS
- migration reasons: []
- Phase 14 Approved-78 formal Gate: PASS

Output:

- `artifacts/phase14_approved78/14_approved78_formal_gate.json`

### Calibration diagnostic caveat

The saved Approved-78 Scene artifacts contain:

- 695 total regions
- 695/695 semantic role = `foreground`

The older GeometryOptimizer has no dedicated `foreground` angularity target and therefore falls back to 0.5.
For rectangle/capsule candidates this makes semantic cost structurally 0.5.

Observed diagnostic metrics:

- mean coverage: 0.998299
- mean silhouette: 0.998299
- mean complexity: 1.358273
- mean angularity: 0.339568
- mean semantic cost: 0.5
- capsule rate: 0.660432
- rectangle rate: 0.339568

An early Phase 14 runner incorrectly applied an implicit `CalibrationTargets()` profile as a formal Gate and produced a false FAIL on angularity/semantic cost.

This was corrected after re-reading `PHASE10_APPROVED78_CALIBRATION.md`:

- CalibrationTargets must be explicitly supplied.
- Hidden/guessed default target profiles are prohibited.
- CalibrationHarness dimensions are diagnostic/policy-comparison data.
- Approved-78 formal migration authorization is owned by `MigrationGate`.

The final runner preserves these diagnostics without weakening or inventing thresholds.

## Phase 12 metadata consistency

The Phase 12 selected-candidate ordering is:

1. fewest passing primitives
2. highest silhouette IoU
3. fewest vertices

The validation metadata string was corrected to match this actual ordering:

`fewest-primitives-then-highest-silhouette-then-fewest-vertices`

Raden and Kyoko were then regenerated in strict order:

Phase 12 -> Phase 13 -> Phase 14

All provenance chains passed after regeneration.

## Tests

Phase 14-specific:

- `tests/zerobase/test_phase14_evaluation.py`
- machine + human PASS
- human FAIL overrides numeric PASS
- deterministic repeat evaluation
- case artifact writer
- corpus fail-closed behavior
- duplicate case rejection

Artifact bridge + Phase 14:

- 24/24 PASS

Relevant broad regression:

- 106/106 PASS

Additional checks:

- new Phase 14 modules/runners compile
- `git diff --check`: no whitespace errors
- only existing CRLF conversion warnings were reported

## Incidents / lessons

### 1. Hidden CalibrationTargets used as formal Approved-78 Gate

Cause:

The first Phase 14 Approved-78 runner treated the dataclass default CalibrationTargets as canonical formal thresholds.

Impact:

Approved-78 incorrectly failed on:
- mean angularity 0.339568 < 0.55
- mean semantic cost 0.5 > 0.22

Fix:

Read the Phase 10 canonical calibration contract, separated diagnostic calibration from formal MigrationGate authorization, and retained the failed diagnostic values instead of hiding them.

Prevention:

Never promote a default/test calibration target to a corpus Gate unless a canonical explicit target profile is present.

### 2. Duplicate Drive filenames

Approved-18 input searches returned duplicate files with identical names.

Fix:

Never selected by filename alone.
Downloaded through the Google Drive connector and verified every input/reference against manifest SHA-256 before evaluation.

Prevention:

Approved corpus retrieval must always use manifest hash binding.

## Phase 14 closure

All required Phase 14 contracts pass:

- Diagnostic-2 visual/machine/determinism Gate: PASS
- Approved-18 regression Gate: PASS
- Approved-78 formal MigrationGate: PASS

Therefore:

**Phase 15 entry is authorized.**

Phase 15 must now own production integration, smoke tests, rollback readiness, development/production output consistency, and the final migration Gate.
