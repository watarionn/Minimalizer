# Phase 8 — Importance / Omission Policy

Status: CLOSED / PASS

Date: 2026-09-29

## Goal

Decide which Phase 7 semantic masses must be protected, kept, or may become omission candidates without reinterpreting semantic ownership or using area alone as a deletion rule.

Canonical actions:

- `protect`
- `keep`
- `prune`

## Independent dimensions

Each mass is scored independently on:

1. silhouette contribution
2. part role
3. identity contribution
4. visual salience
5. redundancy

A prune action requires explicit same-part redundancy evidence plus multiple low-importance grounds. Small area by itself is never sufficient.

## Hard guards

Phase 8 protects:

- every unbound mass as unresolved uncertainty
- face masses
- `accessory_or_held_object` masses
- the largest mass of every present bound semantic part

It does not reinterpret unbound masses, repair Phase 7, generate pixels, inpaint, or complete hidden geometry.

## Outputs

- `08_importance.json`
- `08_importance_heatmap.png`
- `08_pruned_masses.png`
- `08_removed_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

`08_importance.json` records the five score dimensions, canonical action, omission rationale, low-importance grounds, review status, and explicit redundancy evidence including the referenced same-part mass.

## Diagnostic-2

### Hyakuto-Kyoko

- masses: 201
- protect: 141
- keep: 17
- prune: 43
- prune pixel ratio: 0.005032
- silhouette boundary retention: 1.0
- identity prune violations: 0
- unbound prune violations: 0
- invalid prune evidence: 0
- largest-part protection violations: 0
- accessory mass `mass-0152`: protect
- provenance artifacts: 49
- provenance gate: PASS

Visual QA: PASS. Major silhouette, face/hair separation, torso/arms, long hair, goggles and green tie remain readable. Removed content is concentrated on small redundant fragments.

### Juufuutei-Raden

- masses: 93
- protect: 64
- keep: 10
- prune: 19
- prune pixel ratio: 0.001166
- silhouette boundary retention: 1.0
- identity prune violations: 0
- unbound prune violations: 0
- invalid prune evidence: 0
- largest-part protection violations: 0
- accessory mass `mass-0007`: protect
- provenance artifacts: 49
- provenance gate: PASS

Visual QA: PASS. Long hair, face, torso, sleeves, raised arm, rod and major decorative cluster remain readable. Existing unbound uncertainty remains visible and protected.

## Determinism

- Hyakuto-Kyoko: 7 / 7 Phase 8 artifact SHA matches
- Juufuutei-Raden: 7 / 7 Phase 8 artifact SHA matches

Final provenance hashes:

Hyakuto-Kyoko:
- `run.json`: `ef28a7111440b87cf5348d56f4d8ff0c62089119cb2cd3c594ee08b2b24458c5`
- `artifacts.json`: `c0e8d383fcad3dcf081517eefbd837ed778f746f04f6afa3f14e4bb234018b96`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

Juufuutei-Raden:
- `run.json`: `a5fd374d0ce6d15ef0330d18969f5866c8aef8a7a53ecc8e15359c5963714a1b`
- `artifacts.json`: `f4a28aceff264571c618a412bada6684b4fb08299a7018defda9787666cfbcfb`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

## Validation

- focused Artifact Contract / Stage Bridge / Phase 8: 30 passed
- full ZeroBase suite: 141 passed
- stable/Web regressions: 131 passed
- Phase 16 corpus gate: PASS
- real-server smoke: PASS
- final marker: `LOCAL_MERGE_VALIDATION_PASS`

## Provenance

The Stage Contract Bridge now supports `max_phase=8` while preserving existing Phase 6 and Phase 7 behavior. Phase 8 SHA-binds every Phase 7 declared output plus `stage.json` before writing its own artifacts.

## Safety boundary

Unchanged:

- Phase 3-7 artifact bytes
- production Minimalizer 2.0 routing
- analyzer/render authority
- generative/inpainting prohibition

## Next phase

Phase 9 Palette Consolidation may consume Phase 8 protect/keep/prune metadata. It must preserve protected identity and semantic contrast while consolidating shading/wrinkle color variation.
