# Differentiable Minimalization

Status: EXPLORE -> PoC ACTIVE

## Non-negotiable boundary
This is a post-Scene optimization/evaluation layer. It may move/resize/simplify already generated primitives and Bezier control points. It must never use img2img, Generative Fill, diffusion, or another image generator to redraw pixels. DINO/SAM are observers only.

## Loop
source -> existing Minimalizer -> VectorScene -> render -> observe/compare -> optimize primitive parameters -> rerender -> identity/minimality/complexity gate -> accept only on improvement.

## Objective
Minimize:
L = 3*L_silhouette + 1*L_palette + 2*L_semantic + .12*N_primitive + .35*L_tiny + .08*C

The initial weights are hypotheses, not production constants. Identity and silhouette are hard acceptance guards so a lower scalar loss cannot buy a recognizable-subject regression.

## Backends
1. diffvg: primary differentiable rasterizer PoC. Optimize existing geometry only.
2. DINOv3: frozen perceptual/semantic feature observer. No generation.
3. SAM 3/3.1: frozen concept-mask observer for subject/hair/clothes/object/background. No generation.
4. Mitsuba: HOLD for the first 2D SVG PoC. Revisit only for observation/render experiments where it beats the simpler SVG/diffvg path.

## A/B protocol
A = canonical current output. B = same VectorScene after refinement.
Required report: silhouette IoU, semantic feature similarity, palette distance, primitive count, tiny-shape ratio, complexity, wall time, and render determinism.
Adopt only if B passes identity/silhouette guards and improves the joint objective across the benchmark rather than one cherry-picked image.

## Staged PoC
P0: objective/acceptance contract, no new runtime dependency.
P1: diffvg adapter behind optional dependency and feature flag.
P2: geometry-only optimization on rectangle/ellipse/polygon parameters.
P3: frozen DINOv3 feature loss.
P4: SAM concept masks as regional weighting/guards.
P5: Approved corpus A/B and decision.

No stage is allowed to mutate the existing production path by default.


## P2 result — geometry contract PASS (2026-10-03)

P2 is complete at the backend-neutral contract level.

- Existing VectorScene is the only geometry authority entering refinement.
- Refinement may change parameters only for the current supported flat primitives.
- Primitive identity, fill, z-order and primitive count remain fixed in this stage.
- Unknown primitives/proposals fail closed.
- A backend protocol keeps diffvg optional; production does not import it eagerly.
- A finite-difference smoke backend is test-only/research scaffolding, not the intended production optimizer.
- Focused P0+P2 suite: 6/6 PASS on the isolated worktree.

Next: P3 adds frozen semantic observation. DINOv3 must return losses/features only and must never mutate Scene/VectorScene or pixels. Geometry candidates still pass the hard identity/silhouette acceptance gate before adoption.


## P3 result — frozen semantic observer contract PASS (2026-10-03)

P3 is complete at the production-safe observer boundary.

- DINOv3 is observation-only and optional; no eager runtime dependency is introduced.
- The observer returns immutable global and patch feature observations only.
- Semantic loss uses cosine distance over aligned global/patch features.
- Identity ratio is derived for the existing hard acceptance gate; the observer cannot accept candidates itself.
- Missing DINOv3 configuration fails closed without changing the canonical production path.
- Focused P0+P2+P3 suite: 10/10 PASS on the isolated worktree.

Official DINOv3 supports class-token and dense patch-token representations and recommends frozen features as a strong default. The actual heavyweight model/weights remain a research-runtime concern, not a Minimalizer production dependency.

Next: P4 introduces segmentation observations as regional weights/guards. Segmentation remains observation-only: masks may weight losses but may never synthesize, inpaint, redraw, or mutate source/rendered pixels.


## P4 result — regional observation/guard contract PASS (2026-10-03)

P4 is complete at the production-safe segmentation boundary.

- SAM-family integration is optional, frozen, and observation-only.
- Observations expose semantic label, coverage, and confidence; there is no mutation/generation API.
- Regional retention prevents global metrics from hiding local collapse.
- Critical regions default to subject, hair, clothes, and object; thresholds remain research hypotheses until corpus calibration.
- Low-confidence observations are excluded from hard guards rather than treated as truth.
- Regional losses can be importance-weighted independently of the hard retention gate.
- Focused P0+P2+P3+P4 suite: 14/14 PASS on the isolated worktree.

Synthetic guard check: subject retention 0.98 with hair retention 0.50 is rejected, demonstrating that a locally destructive refinement cannot pass merely because the global subject silhouette remains strong.

Next: P5 runs the canonical Approved corpus A/B. Report identity/silhouette/regional retention, semantic loss, palette, primitive/tiny-shape/complexity, runtime and determinism. Adopt only on aggregate improvement with hard guards satisfied; otherwise HOLD/REJECT and preserve the useful observer contracts independently.
