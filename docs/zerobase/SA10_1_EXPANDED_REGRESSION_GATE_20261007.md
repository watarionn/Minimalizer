# SA10.1 Expanded Regression Gate — 2026-10-07

Status: IMPLEMENTED / DIAGNOSTIC ENVELOPE PASS / HARD-GATE AUTHORITY PRESERVED

## Goal

Integrate the precedent-derived regression diagnostics without allowing an aggregate score to hide an existing hard failure.

## Implementation

Added:
- `minimalizer_zerobase/evaluation/expanded_regression_gate.py`
- `tests/zerobase/test_sa10_expanded_regression_gate.py`

The SA10 envelope preserves the canonical hard-gate report verbatim and exposes these diagnostics independently:
- semantic retention
- adaptive complexity
- component survival
- primitive economy
- SA9 teacher coverage
- SA9 primitive-role disagreement count

Unavailable evidence remains explicitly UNAVAILABLE.

## Authority

`pass_gate` is exactly the canonical hard-gate result.

Diagnostics:
- cannot rescue a hard failure;
- cannot independently fail a passing hard gate in SA10.1;
- remain visible separately rather than being collapsed into an aggregate quality score;
- require cross-case calibration before any future promotion.

GC001 teacher coverage 0.25 is therefore diagnostic evidence only.

## Verification

Focused SA10 + canonical hard gate + SA9:
- 21/21 PASS

Expanded relevant suite including multi-component background, adaptive primitive budget, semantic retention observer, and SA10:
- 30/30 PASS

The full `tests/zerobase` directory currently exits 1 during collection with no pytest output on the isolated worktree. The same SA10 and related test files collect and pass when invoked explicitly, so this is recorded as an environment/suite-collection issue rather than silently reported as a full-suite pass.

## Decision

SA10.1 is safe to merge as a diagnostic envelope. Next: SA10.2 should wire deterministic metric adapters from existing reports into the envelope, still without thresholds or aggregate gating.
