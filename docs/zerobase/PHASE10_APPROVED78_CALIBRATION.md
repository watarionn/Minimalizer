# Phase 10 — Approved-78 Calibration

Status: CLOSED
Canonical benchmark: Approved-78, revision 2026-09-18
Entry commit: 3539a0e

## Scope
Phase 10 binds the fixed Approved-78 corpus to saved canonical Scene/candidate artifacts and adds deterministic, inspectable calibration evaluation over Phase 9 GeometryOptimizer outputs. Reference images remain outside Git.

## Implemented
- exact 78-file benchmark manifest using the canonical Google Drive filenames
- ApprovedReference / Approved78Binding contracts with fail-closed corpus validation
- explicit saved Scene/candidate artifact paths for every benchmark item
- CalibrationCase, CalibrationMetrics, CalibrationTargets, and CalibrationResult contracts
- Approved78CalibrationHarness baseline evaluation over independent dimensions
- deterministic policy comparison with stable tie-breaking
- manifest loader and canonical filename regression tests
- duplicate/unbound/empty case rejection

## Reported dimensions
- selected mean coverage
- selected mean silhouette preservation
- selected mean complexity
- selected mean angularity
- selected mean semantic-target cost
- candidate quality-gate rejection rate
- primitive-family selection rates

## Calibration safety
No new GeometryObjectivePolicy weight or semantic target is promoted merely because it improves a composite score. The harness exposes raw dimensions and keeps Phase 9 hard coverage/silhouette gates intact.

The repository does not currently contain the 78 saved canonical Scene/candidate artifact pairs. Therefore Phase 10 does not fabricate corpus measurements and does not claim an evidence-backed weight change. CalibrationTargets must be supplied explicitly; there is no hidden or guessed default target profile.

This is a deliberate calibration result: retain the Phase 9 baseline policy until real Approved-78 replay artifacts exist. Artifact capture belongs to the Phase 11 production-pipeline integration, where the end-to-end deterministic path can persist replayable Scene/candidate snapshots without committing benchmark image binaries.

## Verification
- ZeroBase suite: 53 passed
- canonical manifest count: 78
- first/last canonical filenames: verified
- ungrounded default target profile: prohibited
- production import boundary remains isolated
- reference images are not committed to Git

## Phase 10 decisions
- Approved-78 remains the fixed positive benchmark.
- Google Drive remains the authoritative reference-image store.
- Git stores only the binding manifest and replay/evaluation code.
- No weight tuning is accepted without replayable corpus evidence.
- Phase 9 baseline objective policy remains active for entry into Phase 11.
- Phase 11 must persist canonical replay artifacts as part of production-pipeline assembly, then run this harness before any production policy promotion.

## Phase 11 entry
AUTHORIZED. Phase 11 owns the end-to-end production pipeline and runtime placement. It must preserve the analyzer-independent replay boundary and must not connect ZeroBase to the current production entry point until explicit migration gates pass.

Exact first action: define a ProductionPipeline orchestration contract that wires analyzer evidence -> fusion -> reconstruction -> importance -> palette/material -> candidate generation -> optimization -> composition, with serialized stage artifacts and deterministic replay mode. The first integration test must run without network/model downloads using deterministic baseline adapters.

