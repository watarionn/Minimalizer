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


## P5 checkpoint — corpus gate ready, real refinement A/B HOLD (2026-10-03)

The canonical evaluation assets were verified before making an adoption claim:

- GitHub defines Approved-18 as the medium regression gate and Approved-78 as the formal calibration/final gate.
- Google Drive remains the authoritative image-binary store; the canonical Approved-78 ZIP is present there.
- The local canonical project still contains all 78 replay directories with saved VectorScene/SVG artifacts, plus the Approved-18 source/reference/evaluation assets.

A fail-closed A/B decision contract is now implemented. It reports accepted/rejected, improved/regressed, guard failures, determinism and mean objective delta. Crucially, a composite-score improvement may no longer hide a regression in silhouette, palette, semantic, tiny-shape, complexity, or primitive count. This rule was added after a synthetic P5 test exposed exactly that masking failure mode.

Focused P0-P5 contract suite: 17/17 PASS on the isolated worktree.

### Decision

**HOLD**, not ADOPT and not REJECT.

Reason: the canonical corpus/replay evidence exists, but the actual differentiable renderer/runtime remains P1 HOLD. Therefore there is not yet a genuine B image/VectorScene produced by gradient refinement across Approved-78. Fabricating B measurements from synthetic finite differences would violate the benchmark policy and the project's existing rule against ungrounded corpus claims.

Next action: unblock one real differentiable rendering backend (diffvg first), run a small Diagnostic-2/Approved-18 real-image optimization smoke, then run Approved-78 only if that smoke passes. The observer contracts and fail-closed corpus gate remain valid independently of backend choice.


## P2 result — VectorScene geometry refinement PASS (2026-10-03)

P2 now connects the canonical `VectorScene` boundary to differentiable tensors without mutating the input scene. Rectangle `bbox` and ellipse `cx/cy/rx/ry` parameters can be optimized with a research-only analytic PyTorch soft raster backend; the backend interface remains replaceable by diffvg. Geometry is bounded, gradients are checked for finiteness, and clipping is applied before each update.

The focused P0/P2 suite passes **8/8**. Tests prove loss reduction for rectangle and ellipse, preservation of primitive identity/material/topology, rejection of unknown primitive proposals, and non-mutation of the original `VectorScene`. A first rectangle run exposed a weak-gradient basin for distant shapes; widening the soft-raster gradient field improved the 50-step loss from 0.03669 to 0.01002, and the bounded 80-step test meets the convergence gate. This tuning is research-only and does not change production rendering.

Polygon topology is deliberately not tensorized in this step. The current SVG schema represents triangle/trapezoid/convex_polygon as point arrays, so polygon refinement will be added only with winding/self-intersection guards rather than treating unconstrained vertices as safe.

**Decision: P2 PASS for rectangle/ellipse.** Next: P3 frozen DINOv3 semantic/perceptual observation loss, still evaluation-only and never image generation. Polygon refinement remains a guarded subtask before corpus-scale A/B.


## P3 result — frozen DINOv3 semantic observer gate PASS (2026-10-03)

DINOv3 remains an optional, injected, read-only observer. The research contract stores immutable global and aligned patch features, computes cosine perceptual loss, converts that evidence to an identity-retention ratio, and feeds it into the existing hard acceptance gate. The observer cannot render, mutate a Scene/VectorScene, or accept a candidate by itself. Missing runtime configuration fails closed.

The focused P0/P2/P3 suite passes **14/14**. New gate tests prove that a candidate with a lower optimization objective is still rejected when patch-level semantic identity is damaged, while a semantically preserved improvement can pass when the silhouette guard also passes.

This matches the intended use of DINOv3 as a frozen evaluator: Meta describes DINOv3 as producing high-quality dense image features and reports frozen-backbone evaluation across downstream tasks. Actual pretrained weights remain a research-runtime concern and are not introduced as a production dependency.

**Decision: P3 PASS.** Next: P4 observation-only semantic region masks (SAM-family official runtime if available), used only for regional weighting and retention guards. No synthesis, inpainting, redraw, or pixel mutation is permitted.
