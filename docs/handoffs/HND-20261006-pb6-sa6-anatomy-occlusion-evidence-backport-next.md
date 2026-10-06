# HND-20261006 Minimalizer PB6 / SA6 Anatomy / Occlusion Evidence Backport

Date: 2026-10-06
Status: PB5 COMPLETE / PB6 NEXT
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

Restart from current `main`.

PB5 implementation/audit:
- PR #186
- merge SHA: `c27f721a3d403722ca8738620fd3bc26b63e6d42`

Canonical PB5 record:
`docs/zerobase/PB5_SA5_FACE_NEUTRALIZATION_COMPATIBILITY_AUDIT_20261006.md`

PB5 Drive evidence:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB5_SA5_20261006`

Folder ID:
`1qmhijk3ks5IwvToVRMXZvXeck-YrGgVS`

## PB5 closure

Classification:
**NO-OP-BY-DESIGN + COMPATIBILITY PASS**

GC001:
- face pixels: 4,937
- guard reapply changed face pixels: 0
- outside-face writes: 0
- Forbidden Face Detail: 0.0000%
- candidate already SA7.38 guard-equivalent: true
- PB2 face/head production authority: false
- PB3 face recommendation: insufficient-evidence
- PB3 face production action: null
- PB4 promoted production authority: 0
- diagnostics leave guarded raster SHA unchanged: true

Verification on exact merged implementation main `c27f721a3d403722ca8738620fd3bc26b63e6d42`:
- focused face/backport compatibility: 48/48 PASS
- ZeroBase: 723/723 PASS
- compileall: PASS
- git diff --check: PASS

Production face code was not changed.

## PB6 / SA6 Anatomy / Occlusion Evidence Backport — NEXT

Primary precedents:
- LayerPeeler
- SuperSVG
- LIVE layer reasoning

### Goal

Backport structured anatomy/occlusion **observer evidence** around the existing SA6 anatomy/topology hard boundary without replacing its authority.

PB6 should explain:
- which anatomy roles overlap/touch/disjoin;
- which required topology constraints already exist canonically;
- whether observed mask relations support, contradict, or are irrelevant to canonical topology;
- whether an occlusion direction is unavailable, ambiguous, or merely observed from an existing canonical z-order;
- whether any relation has production authority.

PB6 should not decide anatomy from overlap alone.

### Canonical anatomy authority to preserve

Implementation:
`minimalizer_zerobase/semantic_abstraction/anatomy_guard.py`

Current hard guard:
`anatomy_integrity_gate(baseline, candidate)`

Existing protected conditions:
- required anatomy parts remain present;
- anatomy parts are not suppressed;
- required topology constraints remain present;
- extreme limb bbox changes fail;
- unsafe candidate falls back to baseline.

Existing focused tests:
`tests/zerobase/test_semantic_abstraction_anatomy_guard.py`

PB6 must not weaken or bypass this path.

### Existing observer assets

PB2:
`minimalizer_zerobase/analyzers/structured_mask_evidence.py`

Available relation states:
- OVERLAP
- TOUCHING
- DISJOINT

Direction provenance:
- unavailable
- partial_canonical_z_order
- ambiguous_equal_canonical_z_order
- canonical_z_order_observation
- not_applicable

PB2 relations are observer-only and `production_authority=false`.

SA7.47 compatibility wrapper:
`minimalizer_zerobase/semantic_abstraction/layer_occlusion_evidence.py`

PB4:
semantic debug board can expose observer/advisor/promoted authority separately.

### Preferred PB6 architecture

Canonical `AbstractionPlan` topology
+ PB2 role-mask relation Evidence
+ optional existing canonical z-order observation
-> PB6 Anatomy/Occlusion Diagnostic
-> relation-to-topology compatibility report
-> anatomy guard remains final authority

PB6 diagnostic output must be non-authoritative.

### Suggested per-relation diagnostics

For each anatomy-relevant pair:
- role A / role B;
- source relation;
- overlap/contact pixels;
- optional front/back;
- direction source;
- matching canonical topology constraint, if any;
- compatibility:
  - SUPPORTING
  - NEUTRAL
  - POTENTIAL_CONFLICT
  - INSUFFICIENT_EVIDENCE
- authority state;
- production action = null.

Important:
a `POTENTIAL_CONFLICT` is diagnostic HOLD evidence only.
It must not rewrite topology.

### Anatomy-relevant roles

At minimum inspect:
- head
- torso
- left_arm
- right_arm
- lower_body

Additional roles may provide context:
- hair
- major_clothing
- accessory_or_held_object
- face

Context roles must not become anatomy authority.

### Relation interpretation boundary

Examples:

- canonical `left_arm attached_to torso` + source TOUCHING:
  supporting evidence

- canonical required attachment + source DISJOINT:
  potential conflict / diagnostic only

- source OVERLAP with no canonical depth relation:
  insufficient evidence for front/behind

- canonical z-order supplied:
  may report observed front/back provenance
  but must not mutate z-order

- hair/head overlap:
  semantic overlap evidence, not limb anatomy authority

### Required tests

1. supporting touch relation can be reported without changing anatomy plan.
2. disjoint relation against required attachment becomes diagnostic conflict only.
3. overlap alone never invents front/behind.
4. optional canonical z-order is observed but never changed.
5. anatomy guard pass remains pass after PB6 diagnostic generation.
6. anatomy guard failure remains failure even with perfect observer support.
7. missing required topology cannot be rescued by PB6 evidence.
8. observer/advisor evidence cannot create anatomy parts.
9. mapping/input order is deterministic.
10. PB6 generation does not mutate baseline/candidate plans.
11. PB6 generation does not change production output.
12. existing anatomy guard tests remain unchanged and passing.

### GC001 audit

Use current canonical Phase 4 role masks.

Required:
- build anatomy-relevant PB2 relation graph;
- classify relation compatibility against current semantic topology where available;
- record unavailable/ambiguous direction explicitly;
- confirm production authority count remains 0;
- confirm anatomy guard output is unchanged by diagnostics;
- preserve JSON/debug evidence to Drive.

### Expected classification

Likely:
**IMPLEMENTED + OBSERVER-ONLY DIAGNOSTIC**

PB6 may also close as **NO-OP-BY-DESIGN** if the existing PB2/PB4 evidence already provides all useful anatomy audit information and no distinct diagnostic gap exists.

Do not force a new implementation merely to avoid a no-op classification.

## Hard boundaries

- anatomy/topology guard remains authoritative;
- overlap does not imply attachment or depth authority;
- observer evidence cannot create missing anatomy;
- observer evidence cannot rescue missing/suppressed anatomy;
- no Golden/v12 production authority;
- no generative decomposition;
- no direct z-order mutation;
- no production action from PB6 diagnostic alone.

## Preferred implementation order

1. Inventory anatomy guard/topology schema and current tests.
2. Define the smallest anatomy/occlusion compatibility diagnostic, only if useful.
3. Reuse PB2 relation Evidence rather than duplicating mask analysis.
4. Add synthetic supporting/conflict/ambiguous cases.
5. Prove anatomy hard failures remain authoritative.
6. Run focused PB6 + anatomy + PB2/SA7.47 tests.
7. Run full ZeroBase.
8. Run GC001 anatomy/occlusion audit.
9. Preserve evidence to Drive.
10. Classify PB6 before PB7 review.

## After PB6

PB7 / SA7 Precedent Integration Review.

PB7 should review what actually changed across PB2-PB6, remove duplicated logic if any, confirm authority boundaries, and decide whether any observer/advisor evidence deserves explicit deterministic promotion before SA8.

## Current state declaration

The canonical continuation point is:

**PB6 / SA6 Anatomy / Occlusion Evidence Backport**
