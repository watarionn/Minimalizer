# ZeroBase Phase 6 - Palette & Material

Status: CLOSED

## Scope
Phase 6 separates canonical base material/color from disposable illumination detail and reduces region colors into an inspectable deterministic palette.
It does not analyze pixels, alter Phase 5 importance rationale, fit geometry, compose layers, prune regions, or render output.

## Contracts
- MaterialEvidence binds normalized base_color and illumination_colors to a canonical region_id.
- PalettePolicy owns tier-sensitive merge distances, palette cap, and illumination disposal policy.
- MaterialAssignment exposes base color, selected palette color, illumination colors, confidence, and consumed importance tier.
- PaletteMaterialEngine consumes canonical Scene plus normalized MaterialEvidence only.
- Unknown or duplicate region references fail closed.

## Material / lighting rule
Illumination colors are recorded for audit but are excluded from palette construction by default.
Base material color remains independently inspectable even after palette reduction.
No shadow, wrinkle, or highlight becomes a drawable region merely because a color observation exists.

## Importance boundary
Phase 6 reads Phase 5 tiers only to control merge aggressiveness.
protect colors resist merging most strongly; preserve colors use an intermediate threshold; disposable colors reduce most aggressively.
Phase 6 never changes the Phase 5 decision record or rationale.

## Determinism
Material evidence is canonicalized by region_id.
Representative selection uses stable importance-tier and region-id ordering, with deterministic distance and color tie-breaking.
apply() returns a new Scene and persists policy plus assignments in provenance.

## Verification
- ZeroBase suite: 31 passed
- MaterialEvidence base/illumination separation: PASS
- input-order/replay stability: PASS
- source Scene immutability: PASS
- Phase 5 importance provenance preservation: PASS
- unknown/duplicate material reference fail-closed behavior: PASS
- production import boundary remains isolated
- git diff --check: PASS

## Phase 6 closure
No user-blocking decision remains.
Phase 7 may consume canonical palette/material assignments when generating primitive candidates.
Geometry must preserve the selected material reference without giving palette reduction geometry-selection authority.

## Phase 7 exact first action
Define PrimitiveGenerator and semantic primitive-family policy over canonical Region geometry plus Phase 6 material assignments.
Generate multiple deterministic candidates per eligible region and expose coverage, silhouette, complexity, and angularity metrics before any winner selection.
