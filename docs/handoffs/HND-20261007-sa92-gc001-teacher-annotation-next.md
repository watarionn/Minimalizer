# Handoff — SA9.2 GC001 Teacher Annotation Audit — 2026-10-07

Status: SA9.1 CONTRACT COMPLETE / SA9.2 NEXT

Read first:
1. `docs/zerobase/SA9_SEMANTIC_GOLDEN_TEACHER_20261007.md`
2. `docs/handoffs/HND-20261007-sa9-semantic-golden-teacher-next.md`
3. `benchmarks/golden/cases/GC001_IMG_1205.semantic.json`

## Goal

Populate and review GC001 role-level SURVIVED / SIMPLIFIED / REMOVED / REAUTHORED teacher annotations using evaluation evidence only.

## Boundary

Do not infer labels from Golden coordinates, masks, colors, raster geometry, or pixel copying. Do not change production inference. If existing evaluation evidence cannot justify a label, keep it unavailable.

## First slice

1. inventory existing GC001 feature-survival / Golden-gap artifacts for role-level decision evidence;
2. define an explicit mapping boundary between feature-level semantic manifest roles and production semantic roles;
3. label only evidence-supported matches;
4. emit a GC001 SA9 teacher report;
5. verify production candidate hash/output is unchanged;
6. preserve evaluation artifacts in the canonical Drive hierarchy;
7. decide whether SA10 receives any diagnostic metric.
