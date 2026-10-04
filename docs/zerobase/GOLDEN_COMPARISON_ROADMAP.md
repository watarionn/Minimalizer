# Golden Comparison Development Roadmap

Status: READY FOR NEXT CHAT

G1 Golden Harness: freeze source/golden/current triplet, schema, hashes, deterministic comparison report.
G2 Semantic Feature Manifest: generic schema plus Case 001 benchmark manifest.
G3 Feature Survival Gate: required/optional/forbidden semantics; fail-closed evidence.
G4 Semantic Feature Budgeter: allocate primitive budget by semantic importance and recognizability rather than pixel area.
G5 Geometry Re-authoring PoC: deterministic macro primitives and category compression grammar. VTracer may fit already-authorized masks, never decide semantics.
G6 Golden Gap Evaluator: semantic, geometry, palette, composition, economy and orphan-contour dimensions. Add feature-level DINO evidence.
G7 Guarded DiffMin Integration: refine accepted authored geometry only; same-renderer baseline; default OFF.
G8 Blind Generalization Gate: evaluate multiple characters unseen by Golden training/design iteration. Adopt only if general improvement survives hard gates.

## Parallel work
Nao: G1 harness + schema/tests; VTracer isolated PoC; feature-level DINO experiment.
Rinka: benchmark authority, visual review, architecture decisions, Golden Gap semantics, independent review and adoption.
Nao works on feature branches. Rinka reviews before merge.

## Research queue
P0 VTracer 1.0
P0 DINOv3 local feature evidence
P1 LIVE progressive allocation
P1 Layered Vectorization architecture study without SDS/generative component
P2 SuperSVG/Morphea comparison
P2 CLIPasso concepts only due licensing/fit constraints

## Gates every stage
focused tests; tests/zerobase regression; deterministic rerun hashes; git diff --check; visual artifact review; Drive preservation of visual/evaluation evidence.
