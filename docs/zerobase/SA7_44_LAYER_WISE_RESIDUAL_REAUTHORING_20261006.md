# SA7.44 Layer-wise Residual Re-authoring — 2026-10-06

Status: IMPLEMENTATION PASS / CANONICAL HARD GATE PASS / VISUAL ADOPTION HOLD

SA7.44 adds a bounded coarse-to-fine residual layer stage above the accepted SA7.43 coarse semantic macro geometry.

Primary precedents:
- LIVE
- SuperSVG
- Primitive
- Geometrize

The implementation preserves the SA7.43 coarse geometry as the base authority and only adds source-supported missing residual layers inside the same semantic role.

## Production contract

Pipeline:

Authorized source semantic mask
-> SA7.43 coarse semantic macro geometry
-> rasterize current coarse geometry per role
-> compute source-supported missing residual
-> connected residual components
-> minimum residual support filter
-> safe polygon fit inside role authority
-> marginal value ranking under a separate residual cap
-> selected residual layers
-> canonical renderer
-> existing face / feature / semantic hard gates

The stage does not:
- refit or delete the coarse SA7.43 geometry;
- increase the SA7.43 base primitive budget;
- use Golden/v12 as production inputs;
- allow residual geometry to cross semantic role authority;
- force unused residual capacity to be consumed.

## Residual budget

Default global residual cap:
- 3

Residual eligibility:
- minimum 24 px
- minimum 1.5% of role source area

Safe residual polygon:
- residual coverage >= 60%
- expansion <= 1.12
- authority spill = 0
- maximum residual polygon vertices = 32

## Marginal value

Candidate ranking uses source-only evidence.

Initial score:

`role_coverage_gain / sqrt(vertex_count)`

This follows the Primitive / Geometrize discipline:
- reward source-supported missing structure;
- explicitly tax geometric complexity;
- prefer simple high-value residual layers;
- do not rank by pixel area alone.

Deterministic tie-breaks:
- retained area
- vertex count
- role
- component index

## Explicit layer identity

`MacroGeometryPrimitive` now records:
- `layer_kind`: base / residual
- `component_index`

Base renderer IDs remain compatible:
- `semantic-macro:<role>:<ordinal>`

Residual IDs are explicit:
- `semantic-macro-residual:<role>:<component_index>`

Canonical macro stage version:
- `sa7.44-v1`

Residual layer version:
- `sa7.44-v1`

Renderer version:
- `sa7.44-v1`

Canonical provenance records the complete residual selection report under:
- `semantic_residual_layers`

## GC001 result

SA7.43 coarse allocation remains unchanged:
- global macro cap: 5
- hair: 1
- major_clothing: 3
- unused base capacity: 1

SA7.44 residual extraction:
- candidate residual layers: 5
- selected residual layers: 3
- all selected roles: major_clothing
- residual global cap: 3
- authority spill for all selected layers: 0

Selected layers:

### component 6
- residual area: 59 px
- retained: 58 px
- residual coverage: 0.983051
- role coverage gain: 0.018029
- expansion: 0.983051
- vertices: 9
- marginal value: 0.00600974
- authority spill: 0

### component 2
- residual area: 73 px
- retained: 73 px
- residual coverage: 1.000000
- role coverage gain: 0.022692
- expansion: 1.000000
- vertices: 18
- marginal value: 0.00534854
- authority spill: 0

### component 5
- residual area: 62 px
- retained: 62 px
- residual coverage: 1.000000
- role coverage gain: 0.019273
- expansion: 1.000000
- vertices: 19
- marginal value: 0.00442144
- authority spill: 0

The selected residual layers are small, source-authorized clothing masses that were not represented by the SA7.43 coarse geometry.

## Fresh canonical hard gate

SA7.44 candidate:

- Feature Survival required signatures: 16
- missing: 0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- face-guard writes outside semantic face mask: 0
- overall SA7.35 canonical hard gate: PASS
- Golden raster used by production scene: false

## Visual delta

SA7.43 -> SA7.44:
- pixel delta: 0.128028%
- changed bounding box:
  - x: 115..238
  - y: 145..189

Golden LAB:
- SA7.43: 25.286020
- SA7.44: 25.275946
- improvement: ~0.010075

Browser fallback v12:
- 16.242237

The actual delta board confirms that the change is localized to small source-supported clothing details. No broad restyling or face change occurred.

## Actual four-way review

Reviewed:
- Source
- Browser fallback v12
- SA7.44 HOLD
- Rinka Golden

Conclusion:
- SA7.44 preserves the SA7.43 coarse composition;
- the residual stage behaves as intended;
- selected layers are localized and source-authorized;
- no new hard-gate failure is introduced;
- Browser fallback v12 remains substantially stronger overall.

Decision:
- residual layer architecture: MERGE
- canonical integration: MERGE
- provenance/debug contract: ACCEPT
- SA7.44 GC001 visual candidate: HOLD
- adopted visual baseline: unchanged
- do not append SA7.44 to accepted visual Version History

## Verification

Focused SA7.44 / macro integration:
- 22/22 PASS

Full ZeroBase:
- 650/650 PASS

Other:
- Python compileall: PASS
- git diff --check: PASS

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_44_20261006_HOLD`

Folder ID:
`1leDBjSuG3hSkKbgHJPRPn0lHJpTUK-C7`

Verified cloud artifacts:

- `GC001_sa744_canonical_multifield_scene.svg`
  - `13tT6l9x4CrXdVmwcK1ij42cibtmDtbqW`
- `GC001_sa744_rendered_before_face.png`
  - `1rxVZrricm7dGT7L2rLCd8G26zCi8XWEK`
- `GC001_sa744_final.png`
  - `1nq09VDN_zbfns3GyD-vGZdDHkSAaDQ_K`
- `GC001_sa744_scene_report.json`
  - `1z_q8e0INu2xzekIMZu3y5iq_tcl_nW44`
- `GC001_sa744_residual_layers.json`
  - `1aLOadkfxjplRtlQrykwf3GTpboCIf0IG`
- `GC001_sa744_gate_report.json`
  - `1weW0n1N_GPKKpCl9h453p7SNGKxU2NCO`
- `GC001_sa744_eval.json`
  - `1Ad571EC7MjnbwpEJ8pPqOF0qpQ16ic7k`
- `GC001_comparison_4way_sa744_hold_20261006.png`
  - `1n4a7Bva0ySSlGD0jSOZHd19yy-AMlX3J`
- `GC001_compare_sa743_sa744_delta_20261006.png`
  - `1jsAMe4AB5TxsalasU_NVKi9j-g51unku`

## Decision

Merge SA7.44.

The important result is the coarse-to-fine source-supported residual mechanism, not the small GC001 scalar improvement.

## Next

SA7.45 Semantic Retention Observer.

Primary precedents:
- CLIPasso
- CLIPascene

Goal:
add an observer-only semantic-retention diagnostic that measures whether simplification preserves the image/role meaning, without granting CLIP or any model production geometry authority.

The observer must:
- remain evaluation-only;
- never control rendering directly;
- preserve deterministic production behavior when unavailable;
- produce inspectable provenance;
- never mask existing hard-gate failures.
