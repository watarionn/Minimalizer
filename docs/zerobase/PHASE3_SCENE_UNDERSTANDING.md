# Phase 3 — Scene Understanding

Status: CLOSED

## Scope
Phase 3 converts normalized analyzer Evidence into deterministic canonical Scene hypotheses. It does not reconstruct final regions, assign preservation importance, choose palette/material, generate primitives, or render output.

## Contracts
- EvidenceFusion accepts only canonical Evidence records.
- FusionPolicy owns deterministic overlap/confidence policy.
- Analyzer-specific classes and raw outputs never enter Scene construction.
- All Evidence in one fusion pass must share one CoordinateSpace and unique evidence_id values.
- Provenance is retained through region evidence_ids and Scene provenance.

## Deterministic fusion
Evidence is sorted by evidence_id before grouping. Spatial grouping uses bbox overlap relative to the smaller box. Semantic conflicts prefer higher confidence; equal-confidence ties use producer then evidence_id. Missing confidence uses the persisted policy default.

Region hypotheses use stable region-NNNN IDs and union bboxes. Subject hypotheses are emitted only for configured subject semantic labels. Non-merged intersecting region hypotheses emit deterministic overlaps relations.

## Definition of Done
- [x] deterministic EvidenceFusion contract exists
- [x] FusionPolicy is explicit and validated
- [x] fusion consumes canonical Evidence only
- [x] duplicate IDs and coordinate-space conflicts fail closed
- [x] semantic conflict and tie-breaking behavior is tested
- [x] input ordering cannot change serialized Scene output
- [x] canonical Region hypotheses preserve evidence references
- [x] configured semantic evidence can produce Subject hypotheses
- [x] spatial Region relations are deterministic
- [x] real Phase 2 baseline Evidence passes through fusion
- [x] no heavy/semantic analyzer is required for closure
- [x] current production import path remains isolated from ZeroBase

## Deferred to owning phases
Region boundary reconstruction/merge is Phase 4. Preservation importance is Phase 5. Material/color interpretation is Phase 6. Geometry candidates and rendering remain later phases. Heavy analyzers may add Evidence later but cannot alter this contract.

## Phase 4 entry
AUTHORIZED after the ZeroBase suite passes and production-import isolation is rechecked. First action: define deterministic RegionReconstructor input/output contracts over canonical Scene/Region hypotheses, then test merge/split/boundary behavior before adding reconstruction heuristics.
