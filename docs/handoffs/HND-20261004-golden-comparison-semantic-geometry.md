# HANDOFF: Golden Comparison / Semantic Geometry Re-authoring

Date: 2026-10-04
Status: DESIGN / RESEARCH COMPLETE, IMPLEMENTATION NOT STARTED
Next action: begin G1 in a new chat.

## Why
Case IMG_1205 exposes the central quality gap. Current Minimalizer mostly compresses pixel regions. The human golden reconstructs meaning into a small set of intentional geometric shapes while preserving identity-critical features.

## Canonical comparison
1. source: user-provided IMG_1205 original
2. golden: Rinka human-designed geometric abstraction
3. current: current Minimalizer output
These must be preserved as Golden Case 001. Binary images live in Drive; GitHub stores schema/manifests/docs, not duplicated benchmark binaries unless later explicitly chosen.

## Key diagnosis
Current output loses or weakens goggles and green necktie, produces irregular torso fragments, and spends geometry on low-value remnants. The problem is budget allocation and semantic geometry authorship, not simply too few primitives.

## Adopted direction
Golden is a decision teacher, not a pixel target. Add Semantic Inventory, Feature Budget, deterministic Geometry Re-authoring, Feature Compression and Golden Gap gates before guarded DiffMin.

## Collaboration
Nao implements isolated feature branches. Initial parallel assignments are Golden Harness, VTracer PoC and feature-level DINO PoC. Rinka owns architecture and independent review.

## Research shortlist
VTracer 1.0; LIVE; DINOv3; Layered Vectorization (architecture only, exclude SDS); SuperSVG; Morphea; CLIPasso concepts.

## Existing safety/quality invariants
No generative reconstruction. Existing semantic authority remains authoritative. DiffMin default OFF. Same-renderer normalization. Required semantic loss is hard FAIL. Visual/evaluation artifacts are preserved to Google Drive.

## Start-next-chat checklist
Read architecture, roadmap, Nao guide and this handoff. Confirm Golden Case 001 assets/hashes. Implement G1 only first, run focused + zerobase regression, preserve evidence, then Rinka review before G2.
