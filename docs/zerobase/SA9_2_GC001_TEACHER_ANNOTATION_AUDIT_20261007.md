# SA9.2 GC001 Teacher Annotation Audit — 2026-10-07

Status: COMPLETE / PARTIAL TEACHER EVIDENCE / PRODUCTION-NEUTRAL / SA10 HARD-GATE HOLD

## Goal

Populate GC001 SA9 teacher decisions only where existing reviewed evaluation evidence supports one of:
SURVIVED / SIMPLIFIED / REMOVED / REAUTHORED.

No label is inferred from Golden raster, coordinates, masks, colors, or geometry.

## Mapping boundary

GC001 has two semantic vocabularies that must not be silently collapsed:

Feature-manifest evaluation roles:
- hair
- eyewear_accessory
- necktie
- uniform
- hair_accessory
- uniform_badges
- armband
- facial_details

Production/source-mask roles used by the SA7.46 / PB6 audits:
- accessory_or_held_object
- face_skin
- hair
- left_arm
- left_leg
- major_clothing
- right_arm
- right_leg

The feature manifest is evaluation authority for feature survival. It is not a production-role remapping table. In particular, uniform -> major_clothing, eyewear_accessory -> accessory_or_held_object, and facial_details -> face_skin are not assumed automatically.

## Evidence-supported annotations

### hair = REAUTHORED

Evidence:
- SA7.43 allocates and constructs coarse semantic macro geometry for hair from source-authorized role evidence.
- SA7.44 explicitly preserves the SA7.43 coarse geometry as base authority.

This is stronger and more precise than SURVIVED or SIMPLIFIED: the production representation is explicitly reconstructed as semantic macro geometry.

### major_clothing = REAUTHORED

Evidence:
- SA7.43 constructs coarse macro geometry for major_clothing.
- SA7.44 adds three selected source-supported residual re-authoring layers inside major_clothing.

Therefore REAUTHORED is directly supported by the implementation/evaluation record.

## Unresolved roles

No four-way teacher label is asserted for:
- accessory_or_held_object
- face_skin
- left_arm
- left_leg
- right_arm
- right_leg

SA7.36 proves historical missing source-supported torso/right-arm masses, but that is not equivalent to a final Golden teacher decision. Face-neutralization proves safety, not whether face_skin is SURVIVED/SIMPLIFIED/REMOVED/REAUTHORED.

## Machine-readable audit

Added:
`benchmarks/golden/cases/GC001_IMG_1205.sa9-teacher.json`

The file records:
- the 8 production roles;
- 2 reviewed REAUTHORED annotations;
- 6 unresolved roles with reasons;
- explicit Golden non-authority flags.

## Verification

Focused SA9/SA9.2:
- 9/9 PASS

The audit builds through `build_semantic_golden_teacher_report`.
Unresolved roles remain `golden_decision=null`.
Production authority remains false.
Production input allowed remains false.
Production output changed remains false.

## SA10 decision

Do not promote SA9 to a hard SA10 regression gate.

Reason:
2/8 production roles have evidence-supported teacher labels. A hard aggregate teacher score would manufacture meaning from six unresolved roles.

Allowed next use:
- diagnostic coverage = labeled_roles / production_roles;
- per-labeled-role disagreement diagnostics;
- no production action;
- no hard-gate override.

## Decision

SA9.2 is complete.

The useful result is not maximum label coverage. It is a reviewed, machine-readable partial teacher audit that preserves uncertainty instead of converting weak evidence into fake certainty.
