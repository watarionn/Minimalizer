# Golden Comparison Architecture v1

Status: DESIGN FREEZE FOR IMPLEMENTATION
Canonical repo: watarionn/Minimalizer
Golden Case 001: IMG_1205
Owner/reviewer: Rinka
Implementation collaborator: Nao

## Goal
Teach Minimalizer the *kind of abstraction decision* demonstrated by a human golden reference, not pixel-copy the golden image.

Success means a blind character that has no golden reference benefits from the same abstraction policy.

## Non-negotiable boundaries
- No generative img2img, generative fill, inpainting, or missing-area generation.
- Golden images are evaluation/decision teachers, never production reconstruction inputs.
- Existing semantic masks and renderer-owned semantic ownership remain authority.
- Grounded-SAM/SAM/DINO are observers/hypothesis sources only.
- A perceptual score must never override identity, silhouette, semantic ownership, determinism, or required-feature hard failures.
- DiffMin remains default OFF and is refinement after geometry design, not the designer.

## Golden Case contract
Each case contains source, golden human abstraction, current Minimalizer output, and a semantic feature manifest.
The manifest records feature role, importance, required/optional/forbidden status, palette role, structural relations, and evaluation regions. It must not encode golden polygon coordinates as implementation targets.

Case 001 key semantics:
- orange hair: required / identity-critical
- goggles: required / identity-critical
- green necktie: required / identity-critical
- navy-white uniform: required / identity-critical
- hair ornament: important
- badges/armband: compressible symbolic features
- facial details: forbidden in minimalized output

## Target pipeline
Source -> Semantic Inventory -> Feature Hypotheses -> Semantic Feature Budget -> Macro Shape Builder -> Feature Compression -> deterministic candidate set -> Hard Gates -> Golden Gap evaluation -> optional guarded DiffMin refinement -> Final Gate.

## Geometry Re-authoring
Do not merely reduce contour vertices. Re-author semantic parts using a deterministic grammar such as polygon, ellipse, ring, ribbon, trapezoid and Bezier silhouette.
Examples are category grammar, not Case-001 hacks: necktie = knot + tapered body; goggles = frame + lenses + bridge; badge = ring + center.

## Golden Gap
Keep dimensions separate:
1. semantic feature survival
2. recognizability
3. geometry abstraction
4. palette-role preservation
5. composition / negative space
6. primitive economy
7. orphan contour penalty
8. feature-level perceptual evidence

Required-feature loss is a hard FAIL and cannot be compensated by a high global DINO score.

## Research adoption
Priority PoCs: VTracer curve/polygon fitting; LIVE-style progressive shape allocation; DINOv3 feature-level evidence.
Research-only concepts: Layered Vectorization macro-to-detail structure, CLIPasso abstraction budget, SuperSVG coarse-to-fine structure, Morphea inspectable hypothesis design.
Do not import generative reconstruction from research projects.

## Generalization rule
No Case-001-specific coordinates, thresholds, colors, names or geometry rules in production algorithms. Case-specific data belongs only in test/benchmark manifests.

## Completion criterion
Golden Case 001 gap improves without hard-gate regression, then the same implementation improves a blind multi-character benchmark without access to those characters' golden images.
