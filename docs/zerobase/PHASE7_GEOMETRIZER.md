# Phase 7 — Geometrizer

Status: CLOSED

## Scope
Phase 7 owns deterministic multi-candidate primitive generation over canonical Region geometry.
It does not select a winning candidate. Winner selection remains Phase 9 Geometry Optimizer authority.

## Implemented
- PrimitiveFamilyPolicy with explicit semantic-role family preferences.
- PrimitiveGenerator consuming canonical Scene/Region only.
- Multiple deterministic candidates for eligible regions.
- Rectangle, trapezoid, triangle, ellipse, capsule, and convex-polygon families.
- Inspectable coverage, silhouette, complexity, vertex-count, and angularity metrics.
- Stable candidate IDs and deterministic ordering.
- Fail-closed malformed geometry handling and configurable tiny-region exclusion.
- No analyzer-specific dependency and no mutation of source Scene.

## Verification
- ZeroBase suite: 36 passed.
- Candidate replay/input-order stability: PASS.
- Source Scene immutability: PASS.
- Semantic family policy tests: PASS.
- Metric tradeoff visibility: PASS.
- git diff --check: PASS.

## Phase boundary
Phase 7 generates alternatives only. It does not use first-candidate-under-budget logic,
does not choose a winner, and does not grant rendering authority to geometry generation.

## Phase 8 entry
AUTHORIZED. Phase 8 owns Semantic Composer assembly, z-order/occlusion semantics,
and deterministic vector-scene composition contracts over canonical data.
