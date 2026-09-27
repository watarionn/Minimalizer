# Phase 9 — Geometry Optimizer

Status: CLOSED

## Purpose
Phase 9 owns deterministic multi-objective winner selection over Phase 7
PrimitiveCandidate records and supplies explicit region-to-candidate selections
to the Phase 8 SemanticComposer.

## Contracts
- GeometryObjectivePolicy keeps objective weights and quality gates explicit.
- CandidateSelectionDecision preserves every raw cost dimension used in selection.
- GeometryOptimizationResult exposes selections, decisions, and policy provenance.
- GeometryOptimizer is the sole Phase 9 selection authority.

## Objective dimensions
- coverage cost
- silhouette cost
- complexity cost
- angularity cost
- semantic angularity-target cost
- undercoverage cost

The weighted score guides search only. Raw costs remain inspectable.

## Quality gates
Candidates below minimum coverage or silhouette are rejected before weighted
ranking. If every candidate for a region is rejected, optimization fails closed.
A low-complexity candidate therefore cannot win by catastrophically dropping
paint/silhouette coverage.

## Determinism
Candidates are grouped by canonical region ID and evaluated in stable candidate
ID order. Equal scores use candidate ID as the deterministic tie-breaker.
No stochastic search is used in Phase 9.

## Authority boundaries
- Phase 7 generates candidates but never selects winners.
- Phase 9 selects winners but never changes Scene, materials, or z-order.
- Phase 8 consumes explicit selections but never rescoring them.
- Phase 10 owns Approved-78 weight calibration.

## Verification
- ZeroBase suite: 48 passed
- quality-gate rejection: PASS
- deterministic tie-breaking/replay: PASS
- source Scene immutability: PASS
- Phase 7 -> Phase 9 -> Phase 8 integration: PASS
- malformed/missing candidate metrics fail closed: PASS

## Closure decision
Phase 9 is CLOSED. Default weights are baseline engineering values only and are
not claimed to be Approved-78 calibrated. Phase 10 may tune weights and semantic
targets using the fixed benchmark while preserving the inspectable cost contract
and quality-gate principle.

Next phase: Phase 10 — Approved-78 Calibration.
