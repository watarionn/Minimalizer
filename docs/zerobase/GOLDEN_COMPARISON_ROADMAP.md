# Golden Comparison Development Roadmap

Status: G2 CLOSED / G3 READY

G1 Golden Harness [CLOSED / PASS]: freeze source/golden/current triplet, schema, hashes, deterministic comparison report.
G2 Semantic Feature Manifest [CLOSED / PASS]: generic schema plus Case 001 benchmark manifest.
G3 Feature Survival Gate [NEXT]: required/optional/forbidden semantics; fail-closed evidence.
G4 Semantic Feature Budgeter: allocate primitive budget by semantic importance and recognizability rather than pixel area.
G5 Geometry Re-authoring PoC: deterministic macro primitives and category compression grammar. VTracer may fit already-authorized masks, never decide semantics.
G6 Golden Gap Evaluator: semantic, geometry, palette, composition, economy and orphan-contour dimensions. Add feature-level DINO evidence.
G7 Guarded DiffMin Integration: refine accepted authored geometry only; same-renderer baseline; default OFF.
G8 Blind Generalization Gate: evaluate multiple characters unseen by Golden training/design iteration. Adopt only if general improvement survives hard gates.

## G1 closure

Merged by PR #72 at main commit `d0c20e896766768ccf22156ffa794edbb3e9781d`.

Canonical Golden Case 001 is bound by role, Drive file ID, and SHA-256 rather than filename alone. The harness is isolated from production behavior and treats the golden as evaluation-only evidence, never as a reconstruction input.

Validation on a clean detached worktree:
- focused Golden Harness tests: 4 passed
- full `tests/zerobase`: 255 passed
- `git diff --check`: PASS
- production behavior changes: none

## Parallel work
Nao: VTracer isolated PoC; feature-level DINO experiment; support G2/G3 schema/tests on feature branches.
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

## G2 closure

G2 adds a generic semantic feature manifest contract plus GC001 authority data without golden geometry coordinates. Required identity features are orange hair, goggles, green necktie, and navy-white uniform. Hair ornament is important/optional; badges and armband are symbolic/compressible; facial details are forbidden/omit. Semantic evaluation regions reference feature IDs only.

Validation before merge:
- focused semantic manifest tests: 8 passed
- full `tests/zerobase`: 263 passed
- `git diff --check`: PASS
- G1/G2 case identity linkage: PASS
- production behavior changes: none

