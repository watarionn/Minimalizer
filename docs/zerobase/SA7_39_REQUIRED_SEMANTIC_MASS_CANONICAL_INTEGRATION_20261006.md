# SA7.39 Required Semantic Mass Canonical Integration — 2026-10-06

Status: CANONICAL INTEGRATION PASS / VISUAL ADOPTION HOLD

SA7.39 removes the evaluation-only raster overlay dependency from SA7.37 by integrating required semantic masses into the canonical VectorScene.

## Production contract

Inputs:
- canonical VectorScene
- source-only RequiredSemanticMass reservations from SA7.37
- authorized semantic masks

No Golden raster, adopted-baseline repair geometry, hard-gate JSON, or missing-signature coordinates are inputs.

Each reservation must:
- use an authorized role from the SA7.37 policy;
- satisfy source coverage >= 0.65;
- satisfy expansion ratio <= 1.12;
- report zero role spill;
- rasterize fully inside its semantic role mask;
- overlap none of the protected semantic roles:
  - face
  - head
  - hair
  - major_clothing
  - accessory_or_held_object

Cross-role reservation overlap is forbidden.

Small polygon overlap inside the same semantic role is allowed because palette-cluster contour approximations can meet at their boundaries. Same-role order is deterministic:
- larger mass first;
- smaller local mass later.

Existing scene primitives are never mutated. Reservations are appended as late foreground primitives.

## GC001 integration

Source-only SA7.37 extraction produced 6 reservations:
- left_arm: 2
- right_arm: 1
- torso: 3

All six passed protected-role overlap guards.

A 14-pixel polygon overlap existed only between the two left_arm reservations. No cross-role reservation overlap existed.

Canonical scene:
- primitives before reservation stage: 16
- required semantic masses added: 6
- primitives after: 22
- Golden raster provenance: false

The final pipeline used for evaluation was:

Source-derived semantic scene
→ canonical macro stage
→ canonical background stage
→ SA7.37 required semantic mass extraction
→ SA7.39 canonical reservation integration
→ SVG renderer
→ SA7.38 deterministic face raster guard
→ final PNG
→ SA7.35 canonical hard gate

No SA7.37 research raster overlay is used in this pipeline.

## Fresh hard-gate result

- required source-supported signatures: 16
- Feature Survival: missing=0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- overall canonical hard gate: PASS
- face pixels changed outside semantic face mask: 0

This reproduces the SA7.37 + SA7.38 safety result without the research-only survival overlay.

## Visual evidence

- Visual Delta vs adopted baseline: 71.4836%
- pixel delta vs SA7.38 research candidate: 0.8659%
- SA7.38 -> Golden LAB MAE: 32.3803
- SA7.39 -> Golden LAB MAE: 32.4133
- Browser fallback v12 -> Golden LAB MAE: 16.2422

The canonical scene integration introduces only a small visual change relative to the SA7.38 research candidate while preserving both hard gates.

LAB remains diagnostic/supporting evidence only. Actual four-way review remains authoritative for visual acceptance.

## Decision

Merge the generic canonical scene integration.

Do not update the adopted visual baseline.
Do not append SA7.39 to accepted Minimalizer Version History because the Browser fallback v12 regression floor remains unmet.

## Next

SA7.40 Remaining Gap Re-attribution.

With background composition, source-supported feature survival, and face neutralization now restored in one canonical path, re-run role-local Golden-gap attribution on the SA7.39 final candidate. The next visual work should target the largest remaining semantic/compositional errors rather than continue tuning already-passing safety layers.
