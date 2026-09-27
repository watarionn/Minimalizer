# Phase 4 — Region Reconstruction

Status: CLOSED candidate

## Scope
Phase 4 reconstructs deterministic canonical regions from Phase 3 Scene/Region hypotheses.
It does not rerun analyzers, mutate Evidence, select final primitives, or decide importance.

## Contract
`RegionReconstructor.reconstruct(Scene) -> Scene` consumes canonical data only.
The output preserves schema/coordinate space, Evidence provenance, palette, and valid Subject references.
Reconstruction policy is explicit and serialized into Scene provenance.

## Deterministic reconstruction
1. Sort source regions by stable IDs.
2. Normalize boundaries against the canvas and discard zero-area/outside regions.
3. Split explicit canonical `geometry.components` into stable region hypotheses.
4. Merge only same-semantic regions meeting the configured overlap threshold.
5. Reassign canonical region IDs deterministically.
6. Remap Subject region references and rebuild overlap relations.

## Definition of Done
- canonical Scene-only input/output boundary: PASS
- no analyzer-specific types in regions module: PASS
- source Scene/Evidence data is not mutated: PASS
- boundary clipping and invalid/empty handling tested: PASS
- deterministic split behavior tested: PASS
- semantic-aware merge behavior tested: PASS
- Evidence IDs survive split/merge: PASS
- Subject references survive reconstruction: PASS
- relations are rebuilt from reconstructed geometry: PASS
- input-order/replay stability tested: PASS
- real SLIC Evidence -> EvidenceFusion -> RegionReconstructor integration: PASS
- current production import boundary remains isolated: PASS
- no heavy ML/network dependency added: PASS

## Deferred to owning phases
Importance/preservation decisions belong to Phase 5.
Base-color/material classification belongs to Phase 6.
Primitive fitting and geometry candidate search belong to Phases 7 and 9.
No broad image-driven split heuristic is added here because Phase 4 must not create a second analyzer authority.

## Phase 5 entry
Phase 5 may consume reconstructed canonical Scene regions and assign preservation importance.
The first action is to define an inspectable ImportancePolicy/ImportanceDecision contract
before adding semantic or identity-accent heuristics.
