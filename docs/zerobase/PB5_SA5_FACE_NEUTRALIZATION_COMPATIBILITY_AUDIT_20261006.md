# PB5 / SA5 Face Neutralization Compatibility Audit — 2026-10-06

Status: NO-OP-BY-DESIGN + COMPATIBILITY PASS

Primary objective:
prove that the precedent-derived PB2/PB3/PB4 observer/debug stack coexists with canonical SA7.38 face neutralization without weakening the image-level face safety contract.

## Decision

PB5 makes **no production face implementation change**.

The existing SA7.38 face raster guard remains the canonical face authority.

Reason:
- it already enforces deterministic post-render face flattening;
- it only writes inside the authorized semantic face mask;
- it derives fill color from actually observed source-face pixels;
- it changes zero pixels outside the face mask;
- it achieves Forbidden Face Detail = 0.00%;
- PB2/PB3/PB4 remain observer/diagnostic layers and do not need face render authority.

Adding a new face-layer implementation would duplicate or weaken an already-correct hard safety boundary.

## Canonical face authority preserved

Implementation:
`minimalizer_zerobase/semantic_abstraction/face_raster_guard.py`

Gate:
`minimalizer_zerobase/evaluation/forbidden_face_detail_gate.py`

Existing focused regression:
`tests/zerobase/test_sa738_face_raster_guard.py`

Canonical SA7.38 record:
`docs/zerobase/SA7_38_FACE_NEUTRALIZATION_RECONCILIATION_20261006.md`

SA7.38 contract remains unchanged:
- current rendered RGB + original source RGB + authorized semantic face mask only;
- no Golden/adopted-baseline pixels as repair authority;
- no generated face content;
- no facial-feature proposal authority;
- no case-specific face coordinates/colors;
- one observed source-face color;
- write only face-mask pixels;
- assert zero outside-face changes.

## PB5 compatibility tests

New compatibility suite:
`tests/zerobase/test_pb5_face_neutralization_compatibility.py`

Coverage:

1. PB2 face/head Evidence remains `production_authority=false`.
2. PB3 unavailable semantic perturbation cannot imply face omission.
3. PB3 perfect semantic score cannot override a face hard failure.
4. PB4 debug board visibly preserves face hard-failure state.
5. PB4 generation leaves guarded face raster byte-identical.
6. SA7.38 guard still writes zero pixels outside the face mask.
7. Guarded raster still yields Forbidden Face Detail = 0.00%.
8. Unavailable observer/advisor paths do not change face output.
9. Arbitrary primitive advice cannot become face geometry authority.
10. PB2/PB3/PB4 diagnostics remain no-op after canonical face guard.

Existing SA7.38 tests are reused without modification.

## Focused verification

Focused suite:
- PB5 compatibility
- SA7.38 face raster guard
- PB4 semantic debug board
- PB3 importance diagnostic
- PB2 structured evidence

Result:
- **48/48 PASS**

## Full verification

Full ZeroBase:
- **723/723 PASS**

Other:
- Python compileall: **PASS**
- git diff --check: **PASS**

No production face code was modified.

## GC001 real compatibility audit

Inputs:
- source: `GC001.png`
- current SA7.44 final candidate
- canonical Phase 4 semantic face mask
- canonical Phase 4 head/hair masks for observer context

### Face raster guard result

Face pixels:
- **4,937**

Guard reapplied to current SA7.44 candidate:
- changed face pixels: **0**
- changed outside-face pixels: **0**

Interpretation:
the current candidate is already byte-equivalent to the canonical SA7.38 guarded face result.

Forbidden Face Detail:
- **0.0000%**

Guarded raster SHA before PB2/PB3/PB4 diagnostics:
- recorded in audit JSON

Guarded raster SHA after PB2/PB3/PB4 diagnostics:
- identical

Diagnostic no-op:
- **true**

### PB2 compatibility

Dedicated face/head/hair structured Evidence was generated for audit only.

Result:
- face/head observer Evidence remains non-authoritative
- all inspected face/head `production_authority=false`

PB2 does not obtain face render authority.

### PB3 compatibility

Face diagnostic:
- recommendation: `insufficient-evidence`
- removal impact: unavailable
- merge impact: unavailable
- production action: null
- primitive advisor status: UNAVAILABLE in real GC001 audit
- hard-fail override: false
- production policy changed: false
- production output changed: false

PB3 does not infer that a face component is removable from size/support.

### PB4 compatibility

Promoted production authority:
- **0**

PB4:
- does not change guarded face bytes;
- does not hide hard failures;
- does not issue face production actions;
- remains diagnostic-only.

## Primitive advisor boundary

Synthetic PB5 verification also supplies a perfect-confidence StarVector-style face primitive suggestion.

Result:
- suggestion remains non-authoritative;
- advisor report `production_output_changed=false`;
- face audit `production_eligible=false`;
- PB3 production action remains null;
- PB3 still cannot promote face geometry.

Therefore an external primitive advisor cannot replace SA7.38 face authority.

## Why PB5 is intentionally a no-op

PB5 was allowed to add observer-only diagnostics only if a concrete audit gap remained.

The audit found no such gap.

The existing architecture already has the right separation:

PB2/PB3/PB4
-> observe / diagnose / explain

SA7.38 face raster guard
-> final image-level face safety authority

Changing production face logic would add risk without adding a missing capability.

Therefore:

**NO-OP-BY-DESIGN is the correct implementation outcome.**

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB5_SA5_20261006`

Folder ID:
`1qmhijk3ks5IwvToVRMXZvXeck-YrGgVS`

Verified cloud artifacts:

- `GC001_pb5_face_compatibility.json`
  - `1ZzNolxaJy5_dArDTukUNQRBILyX1vpcv`
- `GC001_pb5_face_compatibility.png`
  - `1RjtQVs5jgG-v6yIqCQ6lk8m0wyg9hd6n`

## Classification

**NO-OP-BY-DESIGN + COMPATIBILITY PASS**

PB5 is complete.

Production face implementation remains SA7.38 unchanged.

## Next

PB6 / SA6 Anatomy / Occlusion Evidence Backport.

Primary source:
- PB2 layer relation evidence
- PB4 inspectable authority/debug board
- existing canonical anatomy/topology guards

Goal:
add observer-level anatomy/occlusion evidence where it helps explain structure while preserving existing anatomy/topology authority.

PB6 must not:
- derive anatomy authority from overlap alone;
- invent front/behind direction without canonical evidence;
- replace existing anatomy/topology hard guards;
- promote observer/advisor relations directly into production z-order.
