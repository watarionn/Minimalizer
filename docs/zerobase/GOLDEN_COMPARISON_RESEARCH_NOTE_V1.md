# Golden Comparison Research Note v1

Date: 2026-10-05
Purpose: preserve the external-tech shortlist and adoption boundaries for Golden Comparison / Semantic Geometry Re-authoring.

## P0: VTracer
Repository: https://github.com/visioncortex/vtracer
Use: deterministic polygon/spline fitting after Minimalizer has already authorized a semantic mask/region. Evaluate fixed-palette and curve simplification paths.
Do not use: whole-image tracing as semantic authority. VTracer must not decide what identity features matter.

## P0: DINOv3
Repository: https://github.com/facebookresearch/dinov3
Use: observer-only dense/perceptual evidence, especially feature-local crops/regions (goggles, necktie, hair silhouette, uniform) in addition to global evidence.
Do not use: perceptual score to override hard semantic/silhouette/identity/determinism failures.

## P1: LIVE
Repository: https://github.com/Picsart-AI-Research/LIVE-Layerwise-Image-Vectorization
Use: study progressive shape/path allocation and compact layered vectorization.
Adoption mode: port/reimplement useful generic ideas rather than taking environment assumptions as production dependencies.

## P1: Layered Image Vectorization via Semantic Simplification
Repository: https://github.com/SZUVIZ/layered_vectorization
Use: study macro-to-detail ordering, semantic layers, structural buildup followed by refinement.
Forbidden: Stable Diffusion / SDS / any generative reconstruction component. Architecture concepts only.

## P2: SuperSVG
Repository: https://github.com/sjtuplayer/SuperSVG
Use: study coarse-to-fine superpixel/SLIC structure and using superpixels as intermediate geometry rather than final geometry.

## P2: Morphea
Repository: https://github.com/sebastian-software/morphea
Use: compare inspectable hypothesis/intermediate representations, primitive-first reconstruction and ambiguity handling.

## Research concepts only: CLIPasso
Repository: https://github.com/yael-vinker/CLIPasso
Use: study abstraction budgets and semantic preservation under a constrained primitive/stroke count.
Boundary: concepts/research reference only unless licensing and implementation fit are explicitly re-reviewed.

## Minimalizer integration hypothesis
Source -> Semantic Inventory -> observer hypotheses -> Semantic Feature Budget -> deterministic Macro Shape Builder -> Feature Compression -> deterministic candidates -> hard gates -> Golden Gap -> optional guarded DiffMin -> final gate.

## Golden rule
Golden is a teacher of abstraction decisions, never a pixel reconstruction target. No case-specific golden coordinates/colors/thresholds may enter production algorithms. Blind-character improvement is required before adoption.
