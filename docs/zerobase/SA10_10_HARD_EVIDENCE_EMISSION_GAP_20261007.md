# SA10.10 Non-GC001 Hard Evidence & Emission-Gap Policy — 2026-10-07

Status: COMPLETE / HARD EVIDENCE BACKFILLED / SA10.9 DINO CORRECTED

## Critical correction

SA10.9 incorrectly used Phase14 `preview.png` as the DINO candidate. Phase14 `preview.png` is the evaluation sheet, not the Minimalizer production candidate. SA10.10 supersedes those two semantic-retention values with hash-bound measurements against `phase_12/12_final.png`.

Correct production-candidate semantic retention:
- Hyakuto-Kyoko: 0.7709177748262631
- Juufuutei-Raden_stylecal_source: 0.914517616858495

Production candidate hashes:
- Kyoko: `9faec9556f98d21465301f16e2fe674b1ee930f373b2dd6d2ddcb82116d5ab7b`
- Raden: `9911795a0a87a0d227c9b43a86bec8497ca47e6cce60c1ef048027e3fb527c1d`

The SA10.9 preview-sheet DINO evidence remains historical only and is superseded.

## Emission-gap policy

Added `actual_emission_support.py`.
This diagnostic measures actual emitted geometry after drop/rejection, but explicitly does not map into SA10.5 Component Survival or Primitive Economy.

Raden actual-emission context:
- allocated primitives: 2
- emitted: 1
- emission realization: 0.5
- actual component representation: 0.5
- actual primitive support: 1.0

Existing SA10.5 component/economy remain UNAVAILABLE for Raden.

## Source Authority

Added `source_authority_evidence.py`.
PASS requires exact source SHA plus a fresh Phase3-14 provenance bridge PASS.

Both cases:
- source hash match: PASS
- fresh provenance gate: PASS
- provenance artifacts: 86
- Source Authority: PASS

## Anatomy / Topology

Added `structural_hard_evidence.py`.
It reconstructs source and candidate graphs independently and uses the existing anatomy_integrity_gate plus graph_validation/source required-relation preservation.

Kyoko:
- Anatomy: FAIL
- extreme bbox change: left_arm
- missing required topology includes face:inside:head and left_arm:attached_to:torso
- Topology: FAIL

Raden:
- Anatomy: FAIL
- missing anatomy part: head
- missing required topology includes face:inside:head and head:above:torso
- Topology: FAIL

These failures are independent of Phase14 machine/human PASS and are not Phase14 metric relabeling.

## Feature Survival / forbidden face

Remain UNAVAILABLE for both cases because no separately adopted canonical visual baseline is bound. Candidate self-reference is explicitly forbidden.

## Verification

Focused SA10.8-10.10 chain: 19/19 PASS.

Cross-case matrix:
`benchmarks/regression/sa10/SA10_10_cross_case_matrix.json`

SHA-256:
`5dc7d7a549e978980ccc234b2955610c8aa90a7bab417e698df6cba140acec18`

No aggregate score or new calibration threshold was added.


## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_10_20261007_HARD_EVIDENCE`

Drive folder ID:
`1TAPioNcv6T_c4KbvK7F3V08-KgtMXw0U`

Drive API readback verified all five artifacts:
- corrected Kyoko semantic retention
- corrected Raden semantic retention
- Kyoko hard evidence
- Raden hard evidence
- SA10.10 cross-case matrix
