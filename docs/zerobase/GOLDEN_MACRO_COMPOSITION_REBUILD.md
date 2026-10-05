# Golden Bridge Macro Composition Rebuild

Status: CANONICAL REDESIGN / 2026-10-05

## Decision

The current Golden Production Bridge visual output is a visual FAIL. Small tuning is suspended.

The failure is architectural: generic observer roles (hair / face_skin / limb / accessory) are being promoted almost directly into repeated geometry. This bypasses the canonical ZeroBase 2nd Cycle sequence:

Semantic Parts -> Structural Graph -> Major Mass -> Importance/Omission -> Palette -> Part-aware Geometry -> Semantic Composition.

A hard-gate PASS is not evidence of acceptable visual quality.

## Goal

Build a deterministic, non-generative character abstraction compositor that first preserves a readable human macro structure, then spends remaining primitives on identity-bearing features.

Golden images remain evaluation-only. No Golden pixels, coordinates, masks, or geometry may enter production reconstruction.

## Required production order

1. Subject evidence
2. Semantic part evidence
3. Structural graph
4. Macro mass plan
5. Hierarchical primitive budget
6. Part-aware geometry
7. Identity/accent feature attachment
8. Semantic composition
9. Render Sanity Gate
10. Visual/Golden Comparison evaluation

No observer role may directly own final geometry merely because it has a bbox.

## Macro mass contract

The planner must represent, when supported by evidence:
- head mass
- hair mass
- torso / major clothing mass
- left/right arm masses
- lower-body mass
- identity/accent attachments

Each mass carries evidence provenance, confidence, normalized anchor/bbox, relation to parent, required/optional status, and an authorized primitive-family set.

Unknown is allowed. Unsupported anatomy must not be hallucinated.

## Hierarchical budget

Primitive budget is allocated in tiers:
A. readable person skeleton/masses
B. required identity features
C. important optional features
D. compressible decoration

Repeated primitives for the same feature require incremental geometric information. Exact or near-duplicate geometry is forbidden from consuming additional budget.

A 12-primitive candidate that spends 9 primitives on effectively identical hair polygons is a hard economy failure.

## Structural invariants

When evidence supports them:
- head is spatially connected/near torso
- torso is a central major mass
- lower body extends below torso
- arm masses attach to torso/shoulder region
- hair is organized around head rather than used as the whole character silhouette
- accessory/accent geometry attaches to an authorized parent mass

These are relational constraints, not Case001 coordinates.

## Gates

### Macro Readability Gate
Fail if supported major masses collapse into one thin/isolated shape, or if no coherent head/torso/lower-body composition can be formed despite sufficient evidence.

### Primitive Economy Gate
Fail duplicate/near-duplicate geometry and require useful-information gain per extra primitive.

### Render Sanity Gate
Existing gate remains mandatory before any comparison artifact.

### Visual Quality Gate
Human visual FAIL overrides numerical PASS.

## Evaluation cadence

At every major implementation milestone:
1. run fresh blind cases without Goldens;
2. run GC001 diagnostic only after generic implementation is frozen;
3. create comparison by arranging actual Source | Minimalizer | Rinka Golden assets only;
4. never synthesize comparison evidence;
5. save visual/evaluation artifacts to Google Drive under chatGPT及びCodex用/Minimalizer;
6. verify Drive read-after-write.

## Work split

### Rinka authority
- canonical architecture
- macro/visual gates
- blind corpus selection and freeze
- Source/Minimalizer/Golden comparison
- review/adopt/reject
- final merge authority

### Codex / Nao implementation lane
Work from this document and AGENTS.md on separate feature branches:
- implement MacroMassPlan schema + deterministic planner
- implement hierarchical primitive allocator
- implement duplicate-geometry/economy gate
- add synthetic non-GC001 tests
- do not add Case001 names, colors, coordinates, or thresholds

Suggested branches:
- codex/macro-mass-plan
- codex/hierarchical-budget
- codex/primitive-economy-gate

## Acceptance

This redesign is not complete because tests are green. It is complete only when:
- regression suite passes;
- blind characters remain hard-gate safe;
- actual rendered people are structurally readable;
- GC001 actual-output comparison materially closes the gap to the Golden without Golden reconstruction input;
- gains generalize to blind characters.

## Current known failure evidence

GC001 current-main corrected raster passes Render Sanity but remains a visual FAIL: generic role geometry collapses character structure and repeated hair polygons waste the budget. This is the motivating failure, not a target-specific tuning case.
