# SA9 Semantic Golden Teacher — Initial Slice — 2026-10-07

Status: CONTRACT PASS / GC001 AUDIT PASS / EVALUATION-ONLY / SA10 PROMOTION HOLD

## Goal

Add deterministic teacher/evaluation tooling that joins production semantic role names with evaluation-only Golden decision labels while preserving the rule that Golden raster, coordinates, masks, colors, and geometry never enter production inference.

Primary precedents:
- CLIPasso / CLIPascene semantic-retention diagnostics
- StarVector primitive-role agreement diagnostics

## Implementation

New module:
`minimalizer_zerobase/semantic_abstraction/semantic_golden_teacher.py`

Contract version:
`sa9-v1`

Decision vocabulary:
- SURVIVED
- SIMPLIFIED
- REMOVED
- REAUTHORED

The contract accepts only role-level decision annotations and optional primitive-family labels. It deliberately has no fields for Golden raster, coordinates, masks, colors, or geometry.

Authority fields are fixed:
- authoritative=false
- can_override_hard_fail=false
- production_input_allowed=false
- production_output_changed=false

Unknown roles, duplicate Golden roles, authoritative semantic-retention payloads, authoritative primitive-advisor payloads, and observer/advisor roles outside the production role set fail closed.

## Existing evidence inventory

SA7.45 provides:
- global / patch / role-local semantic-retention observations;
- explicit fidelity/simplicity separation;
- observer-only authority.

SA7.46 provides:
- deterministic source-geometry primitive family;
- optional StarVector-style suggestion;
- family agreement;
- advisor-only authority.

PB3 provides:
- component removal/merge semantic-impact diagnostics;
- explicit insufficient-evidence behavior;
- no production action.

## Verification

Focused SA9 + SA7.45 + SA7.46:
- 26/26 PASS

Full ZeroBase:
- 756/756 PASS

The production-no-op test changes the Golden decision for the same role from SURVIVED to REMOVED and verifies the production state is unchanged while only the teacher report changes.

## GC001 teacher audit

Canonical production-side source-mask evidence has 8 inspected roles:
- accessory_or_held_object
- face_skin
- hair
- left_arm
- left_leg
- major_clothing
- right_arm
- right_leg

Existing SA7.45 overall semantic-retention context:
- 0.7298672763136121

Existing SA7.46 real StarVector runtime:
- unavailable
- deterministic source geometry classified the eight inspected roles as polygon
- production promotion count: 0

Existing GC001 semantic manifest uses feature-level evaluation roles such as hair, eyewear_accessory, necktie, uniform, hair_accessory, uniform_badges, armband, and facial_details.

No canonical artifact currently encodes the new SA9 SURVIVED / SIMPLIFIED / REMOVED / REAUTHORED decision labels for all eight production roles. SA9 therefore does not invent those labels from area, palette, coordinates, or Golden pixels.

GC001 audit result:
- teacher schema: READY
- production roles: 8
- canonical SA9 Golden decision annotations: unavailable
- production output changed: false
- Golden production input: forbidden
- SA10 semantic-teacher gate promotion: HOLD pending real teacher annotations

This is fail-safe rather than a failure: the teacher can now represent the decisions, but absence of teacher evidence remains explicit.

## SA10 decision

Do not add a hard SA10 regression gate from SA9 yet.

A future SA10 diagnostic may consume SA9 reports only after role-level Golden decision evidence is populated and reviewed. Existing Feature Survival, face, anatomy, topology, source-authority, expansion, and overlap gates remain individually authoritative.

## Decision

Merge the SA9 teacher contract as evaluation-only infrastructure.

Next:
SA9.2 should populate reviewed GC001 role-level teacher annotations from evaluation evidence without deriving production geometry from Golden pixels. Only after that audit should SA10 diagnostic promotion be reconsidered.
