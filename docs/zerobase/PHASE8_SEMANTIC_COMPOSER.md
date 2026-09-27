# Phase 8 — Semantic Composer

Status: CLOSED

## Scope
Phase 8 owns deterministic semantic assembly of explicitly selected primitive candidates.
It resolves material/fill references, z-order, and occlusion into a canonical VectorScene.
It does not select geometry winners and does not render SVG/raster output.

## Implemented
- SemanticComposer with explicit external region-to-candidate selections.
- CompositionPolicy with background ordering and strict reference controls.
- Canonical ComposedPrimitive and VectorScene contracts.
- MaterialAssignment to fill-reference binding.
- Deterministic in_front_of / behind normalization into occlusion edges.
- Stable topological z-order with background-first and region-id tie-breaking.
- Inspectable occluded_by relationships and composition provenance.
- Fail-closed missing/mismatched candidate, material, relation, and cyclic occlusion handling.
- Input-order/replay stability and source Scene immutability.

## Verification
- ZeroBase suite: 41 passed.
- Explicit-selection authority boundary: PASS.
- Z-order/occlusion normalization: PASS.
- Missing-reference and cycle rejection: PASS.
- Replay/input-order stability: PASS.
- Source Scene immutability: PASS.
- git diff --check: PASS.

## Phase boundary
Phase 8 consumes selections but never creates them. Candidate scoring and winner selection remain
Phase 9 Geometry Optimizer authority. SVG/vector serialization and raster export remain Render-layer work.

## Phase 9 entry
AUTHORIZED. Phase 9 owns deterministic multi-objective candidate selection over the candidate metrics
exposed by Phase 7, while preserving Phase 8's explicit selection/composition boundary.
