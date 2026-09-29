# ZeroBase 2nd Cycle Phase 10 ― Part-Aware Geometrization

Status: **CLOSED / PASS**

Phase 10 is implemented, locally verified, and independently reviewed by Rinka. It is `CLOSED / PASS`. Phase 11 has not started, and Minimalizer 2.0 remains the production standard.

## Scope

Phase 10 consumes the immutable, SHA-bound outputs of:

- Phase 7 semantic masses and mass labels
- Phase 8 `protect / keep / prune` decisions
- Phase 9 palette assignments and source-derived colors

It emits multiple deterministic primitive candidates for every active mass, candidate costs, and one selected primitive per active mass. It does not compose semantic z-order; that remains Phase 11 authority.

## Implementation

- Dedicated generator: `minimalizer_zerobase/geometrization/part_aware.py`
- Artifact writer and deterministic renderers: `minimalizer_zerobase/geometrization/artifacts.py`
- CLI: `tools/run_zerobase_phase10.py`
- Stage Contract Bridge: verified chain extended through `max_phase=10`
- Focused/negative tests: `tests/zerobase/test_phase10_part_aware_geometrization.py`
- Bridge tests: `tests/zerobase/test_stage_contract_bridge.py`

Part-specific candidate families and complexity budgets distinguish face/head, hair, torso/clothing, arms, lower body, accessory/held object, and unbound uncertainty. Available families are polygon, rounded polygon, ellipse, capsule, oriented rectangle, tapered strip, and polyline ribbon. Generic axis-aligned rectangle generation is not available.

Selection uses deterministic coverage loss, spill loss, silhouette loss, complexity cost, and part-family prior with a canonical family-order tie break. Every candidate is bound to its Phase 7 mass, semantic owner, Phase 8 action, and Phase 9 palette entry.

## Hard guards

- Phase 7 geometry and semantic ownership are read-only.
- Phase 8 `prune` remains omitted and cannot reappear as a candidate or selection.
- Unbound masses remain unbound and use uncertainty-specific families.
- Cross-mass candidates and semantic-owner/action/palette changes are rejected.
- Visible output uses deterministic transforms of observed mass geometry and Phase 9 source-derived palette colors only.
- Generation, inpainting, and hidden completion are forbidden.
- Giant selected oriented-rectangle/capsule candidates above 18% of subject area fail validation.

## Mandatory artifacts

Each case emits:

- `10_geometry.json` — primitive candidates, explicit candidate costs, selected set, bindings, policy, validation
- `10_candidate_grid.png`
- `10_selected_primitives.png`
- `preview.png`
- `metrics.json`
- `stage.json`

Canonical development artifacts:

- `artifacts/zerobase2/Hyakuto-Kyoko/phase_10/`
- `artifacts/zerobase2/Juufuutei-Raden/phase_10/`

Persistent diagnostic mirrors:

- `docs/zerobase/diagnostics/phase10/Hyakuto-Kyoko/`
- `docs/zerobase/diagnostics/phase10/Juufuutei-Raden/`

## Diagnostic-2

### Hyakuto Kyoko

- Source SHA-256: `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`
- Active / pruned masses: 158 / 43
- Candidates / selected: 473 / 158
- Mean candidates per active mass: 2.993671
- Mean selected IoU: 0.918284
- Selected families: polygon 75, rounded polygon 66, oriented rectangle 6, tapered strip 4, ellipse 3, capsule 2, polyline ribbon 2
- Provenance gate: PASS, 61 artifacts
- Visual QA: PASS. Head/hair, face, torso, arms, and green tie retain distinct geometry without a giant rectangle/capsule chain.

### Juufuutei Raden

- Source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Active / pruned masses: 74 / 19
- Candidates / selected: 202 / 74
- Mean candidates per active mass: 2.729730
- Mean selected IoU: 0.921663
- Selected families: polygon 59, rounded polygon 8, capsule 4, ellipse 1, oriented rectangle 1, tapered strip 1
- Provenance gate: PASS, 61 artifacts
- Visual QA: PASS. Long hair, face, body/sleeves, arms, and held-object evidence remain distinguishable without a giant rectangle/capsule chain.

Both cases report zero multiple-candidate violations, family violations, complexity violations, missing/orphan selections, prune resurrection, semantic-owner change, cross-mass candidates, giant rectangle/capsule chain candidates, or generated/inpainted pixels.

## Determinism

Independent review/rerun matched all six mandatory artifact SHAs for both cases (6/6 + 6/6), including `stage.json`.

- Kyoko `10_geometry.json`: `11cc0670901143f5c325d9d67d16a89aefd296ee50f9c04b29fb0521f27c20c5`
- Kyoko `10_selected_primitives.png`: `f180436b7fdf6023bd031ad11307a2c657dab578f2a28c3eb3555c8af608d16a`
- Raden `10_geometry.json`: `b2909a710e90901ca0c06d8b8a2e7ab4ea9869642aa7e2460c1df923e4e8e988`
- Raden `10_selected_primitives.png`: `71cd16fbc42101be749f8b98f496bdc28db085a600ce80a00375dd2b3d55c9fa`

## Tests

- Focused Phase 10 + Stage Contract Bridge: **27 / 27 passed**
- Full ZeroBase suite: **167 / 167 passed**

The pytest cache emitted a Windows cache-path warning after the passing run; it did not affect test execution or results.

## Closure boundary

Rinka independent review confirmed focused 27/27, full ZeroBase 167/167, Diagnostic-2 visual PASS, and review/rerun mandatory artifact SHA matches of 6/6 + 6/6. Phase 10 is `CLOSED / PASS`. No commit, push, main merge, production route change, deployment, or Phase 11 work is included.
