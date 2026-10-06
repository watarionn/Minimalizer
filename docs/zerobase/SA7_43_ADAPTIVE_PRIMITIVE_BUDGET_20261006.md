# SA7.43 Adaptive Primitive Budget — 2026-10-06

Status: IMPLEMENTATION PASS / CANONICAL HARD GATE PASS / VISUAL ADOPTION HOLD

SA7.43 replaces the rigid canonical macro-role primitive caps with a deterministic source-supported adaptive allocator while preserving a strict global cap.

Primary precedent:
- AdaVec adaptive parameterization

Supporting precedent:
- Primitive / Geometrize bounded marginal-value selection

No model, CLIP score, VLM, Golden raster, or Browser fallback raster becomes production budget authority.

## Fixed-budget inventory

The SA7.43 inventory found several budget concepts, but only one is on the current canonical SA7 macro rendering path and therefore changed in this stage.

### Canonical macro geometry — changed in SA7.43

Before SA7.43:
- hair max connected macro masses: 3
- major_clothing max connected macro masses: 2
- conceptual total ceiling: 5
- allocation was fixed by role, not by source demand

After SA7.43:
- one global macro cap: 5
- required minimum: hair=1, major_clothing=1
- hard per-role maximum: 3 each
- extra slots compete globally using source-supported major-component area
- unused capacity is allowed to remain unused

### Background field geometry — unchanged

SA7.42 already separates:
- palette cluster cap: 3
- rendered background field cap: 6

It already uses source-supported component selection and remains independent from the SA7.43 macro budget.

### Fine identity geometry — inventoried, not promoted in this stage

`fine_geometry_grammar.py` still contains:
- default fine primitive budget: 10
- category-specific minima such as eyewear=2

This path is not the canonical GC001 macro rendering authority used by SA7.42/SA7.43. It is retained for later focused integration rather than broadly rewritten here.

### Golden Production Bridge semantic budget — inventoried, not changed

`GoldenProductionBridgePolicy.primitive_budget=12` and G4 semantic allocation remain behind the default-OFF production bridge.

They are not the canonical SA7.42/SA7.43 rendered path and therefore were not silently changed.

### Semantic IR min/max constraints — unchanged

`GeometryConstraints.min_primitives/max_primitives` are semantic constraints/schema fields rather than the active global allocator.

## New production allocator

New module:

`minimalizer_zerobase/semantic_abstraction/adaptive_primitive_budget.py`

Primary contract:

1. normalize roles in deterministic lexical order;
2. detect source-supported major connected components;
3. reject tiny fragments below the existing macro component contract:
   - at least 12 px
   - and at least 2% of the source role mask;
4. reserve required minima first;
5. fail closed if the global cap cannot satisfy required minima;
6. create one marginal demand item for each additional major source component up to the role hard maximum;
7. rank marginal demand in one global source frame by:
   - source-supported component area / total source area
   - optional role importance multiplier
   - deterministic role / ordinal tie break;
8. allocate until the global cap is consumed or no supported demand remains;
9. leave unused capacity unused instead of forcing redundant geometry.

The report records:
- required minimum
- hard maximum
- source area
- major component count
- major component areas
- contour vertex telemetry
- complexity telemetry
- allocated primitives
- allocation reasons

## Important implementation correction

The first focused run exposed one design bug in the initial allocator.

Initial ranking used:
`component_area / role_source_area`

That made a small component in one role tie a much larger component in another role whenever both represented the same fraction of their own role.

Example:
- 40x40 hair component
- 80x40 clothing component

Both could appear as "one third of the role" despite very different global source support.

Fix:
rank extra slots by:
`component_area / total_source_area_across_budgeted_roles`

This preserves a shared global reference frame and matches the global-budget contract.

The corrected focused suite passes.

## Canonical macro integration

`macro_geometry_reauthoring.py` now exposes:

- `reauthor_macro_geometry_with_budget(...)`
- legacy-compatible `reauthor_macro_geometry(...)`

Canonical macro stage:
- consumes the adaptive allocator;
- retains the existing geometry safety checks;
- records the full budget report in scene provenance as `semantic_macro_budget`.

Canonical macro stage version:
`sa7.43-v1`

Macro geometry version:
`sa7.43-v1`

## GC001 source-supported allocation

Global macro cap:
- 5

### Hair

- source area: 17,541 px
- major source-supported components: 1
- largest component after existing cleanup: 17,633 px
- contour vertices telemetry: 20
- required minimum: 1
- hard maximum: 3
- allocated: 1
- extra demand: none

Result:
the old role reservation had capacity for up to 3 hair masses, but the source only supports one current macro mass. No redundant extra geometry is forced.

### Major clothing

- source area: 3,217 px
- major source-supported components: 8
- leading component areas:
  - 1,858
  - 314
  - 278
  - 203
  - 97
  - 87
  - 73
  - 65
- contour vertices telemetry: 81
- required minimum: 1
- hard maximum: 3
- allocated: 3

Result:
clothing receives one additional macro slot compared with the old fixed max=2 path.

### Global result

- global cap: 5
- allocated total: 4
- unallocated: 1
- hair: 1
- major_clothing: 3

The allocator does not force the final unused slot into either role because no additional representation is authorized beyond the current hard maximum / supported demand contract.

## GC001 visual delta

SA7.43 changes only a small local clothing-supported area versus SA7.42.

- pixel delta vs SA7.42: 0.232699%
- approximate changed-pixel count: ~269 px
- changed bounding box:
  - x: 102..127
  - y: 149..171

The delta board confirms the change is local rather than a global restyling.

Golden LAB:
- SA7.42: 25.2943
- SA7.43: 25.2860
- improvement: ~0.0083

Browser fallback v12:
- 16.2422

The scalar improvement is intentionally treated as tiny. The important result is that source-supported budget reallocation works without destabilizing the scene.

## Fresh canonical hard gate

SA7.43 final candidate:

- Feature Survival required signatures: 16
- missing: 0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- face-guard writes outside semantic face mask: 0
- overall SA7.35 canonical hard gate: PASS
- Golden raster used by production scene: false

## Actual four-way review

Reviewed:
- Source
- Browser fallback v12
- SA7.43 HOLD
- Rinka Golden

Conclusion:
- SA7.43 preserves the SA7.42 composition;
- the added clothing-supported mass is localized and source-authorized;
- no new face-detail or subject-spill failure is visible;
- Browser fallback v12 still remains substantially closer to the desired overall subject representation.

Therefore:
- adaptive budget implementation: MERGE
- architecture/provenance: ACCEPT
- SA7.43 candidate visual baseline: HOLD
- adopted visual baseline: unchanged
- accepted Minimalizer Version History: do not append SA7.43 as an adopted visual version

## Verification

Focused SA7.43 + macro integration:
- 17/17 PASS

Full ZeroBase:
- 641/641 PASS

Other:
- Python compileall: PASS
- git diff --check: PASS

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_43_20261006_HOLD`

Folder ID:
`1amzsvY0wU47BlsDHK5ivQGjqSwL_YTsS`

Verified cloud artifacts:

- `GC001_sa743_canonical_multifield_scene.svg`
  - `1oocTo5rUBn0fFljPHERSqbRIaEnUpyo9`
- `GC001_sa743_rendered_before_face.png`
  - `1x2Ebhn9DESRf50aoxJJAh1vbJPzyqCiq`
- `GC001_sa743_final.png`
  - `1zTNLD8zobRSMOH1_cDjnTMfZNZQmvIpi`
- `GC001_sa743_scene_report.json`
  - `1xVhlHOCvgZx43HMKQDqqdWVwbST84lR1`
- `GC001_sa743_macro_budget.json`
  - `1eJQlurpM-u2e0NZ-3PdYh18LHEJjNnZP`
- `GC001_sa743_gate_report.json`
  - `11B-7-uEYVq6k8YhF47bzTeYAEwBONXB-`
- `GC001_sa743_eval.json`
  - `12Rsy-AaFalEqFYL4i7m52UcbG7RPq5A-`
- `GC001_comparison_4way_sa743_hold_20261006.png`
  - `11GgOEIhnd-M_59qGBWqhKWoAJoiXQkny`
- `GC001_compare_sa742_sa743_delta_20261006.png`
  - `1XAr_DBphbB2gWLiTI-8NJoi7-LsgLh6X`

## Decision

Merge SA7.43.

The production value is the allocator and provenance contract, not the tiny GC001 scalar gain.

Keep the visual candidate HOLD because the Browser fallback v12 regression floor remains unmet.

## Next

SA7.44 Layer-wise Residual Re-authoring.

Primary precedents:
- LIVE
- SuperSVG
- Primitive
- Geometrize

Goal:
start from the accepted coarse semantic masses, measure source-supported residual structure, and add only bounded residual layers whose marginal representational value justifies their complexity.

Do not broaden the global primitive cap merely to improve scalar fidelity.
