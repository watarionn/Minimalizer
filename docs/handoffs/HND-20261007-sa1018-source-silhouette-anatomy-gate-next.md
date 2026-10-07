# HND-20261007 SA10.18 Source Silhouette & Anatomy Hard Gate NEXT

## Goal
Prevent a production candidate from being called BEST when it changes the source-character geometry or removes a major body part. The triggering GC001 production review showed a rounder face, source-silhouette drift, and missing arms despite a valid production route.

## Start point
SA10.17 repaired the La-Darknesss / Kaela-Kovalskia fragmentation cluster generically by stopping high-cardinality critical owners from forcing raw Phase 11 primitive replay. Existing SA10 regression tests remain green.

## Required work
1. Bind Phase 14 structural authority to source-derived silhouette/anatomy evidence, not only the Phase 11/12 baseline.
2. Add hard-fail checks for major body-part disappearance (at minimum left_arm/right_arm when source evidence says visible), face/head geometry drift, and material outer-silhouette loss.
3. Keep source authority, provenance, topology, face Feature Survival, and current fragmentation threshold unchanged.
4. Add synthetic regressions proving that an omitted arm and a rounded/expanded face are rejected even if aggregate silhouette/primitive economy look favorable.
5. Re-run GC001 IMG_1205 and the existing SA10 regression set. Do not promote a new BEST until the structural hard gates pass.

## Forbidden shortcuts
- No case-name branches.
- No fixed GC001 coordinates/colors/masks.
- No aggregate score as authority.
- No threshold weakening to turn a failure into PASS.
- No generative fill/img2img repair.

## Definition of Done
GC001 no longer accepts the currently reviewed malformed result as BEST; arm visibility and face/head geometry are preserved by generic source-bound hard gates; existing PASS cases remain PASS; evidence and next handoff are preserved in GitHub and required visual artifacts in the established Google Drive Minimalizer hierarchy.
