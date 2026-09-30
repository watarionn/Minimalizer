# Browser Fallback v0

Status: **FUNCTIONAL PASS / QUALITY HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Railway remains the normal hosted fallback until a later quality gate passes.

## Goal

Establish a browser-only emergency path that can eventually replace Railway when Local Worker is unavailable.

The target architecture is:

```text
Browser
  -> Local Worker
  -> Browser Fallback
  -> Railway (temporary final escape hatch)
```

The final product goal is to remove the Railway leg after Browser Fallback reaches an acceptable quality level.

## v0 contract

`web/static/browser-fallback.js` is a deterministic JavaScript engine with:

- no rembg;
- no RTMLib;
- no ONNX/model runtime;
- no network request from the engine itself;
- no generative image processing;
- opaque white-background PNG output, matching the current hosted Standard V2 export contract;
- fixed `analysisMaxSide=400`, `workMaxSide=192`, and `maxShapes=40` in the Web integration.

The current v0 algorithm is intentionally small:

1. decode and resize in the browser;
2. deterministic RGB histogram and palette seeding;
3. weighted k-means palette refinement;
4. per-pixel palette assignment;
5. local label smoothing;
6. connected-component extraction;
7. tiny-component absorption;
8. convex-hull polygon construction;
9. polygon simplification;
10. deterministic Canvas rendering.

This is a fallback prototype, not a JavaScript port of canonical Python V2.

## Routing safety

Browser Fallback is opt-in only.

- default: existing Local Worker / Railway behavior remains unchanged;
- `?browserFallback=1`: Local Worker first, Browser Fallback second, Railway only if Browser Fallback itself fails;
- `?browserFallback=force`: Browser Fallback directly, for development and visual comparison;
- `?browserFallback=0`: remove the persisted Browser Fallback opt-in.

The mode is stored under `minimalizer.browserFallbackMode`.

A Browser Fallback success returns response metadata including:

- `X-Minimalizer-Mode: browser-fallback-v0`
- `X-Minimalizer-Compute: browser`
- `X-Minimalizer-Analysis: deterministic-js`
- `X-Minimalizer-Browser-Fallback-Version: browser-fallback-v0`

## Railway vs unguided Python proxy baseline

Before implementing JavaScript v0, the hosted Railway route was compared with canonical Python V2 without rembg guidance on five cases.

Mean results:

- SSIM: **0.9067**
- edge IoU: **0.5332**
- unguided Python processing: **3879.9 ms**
- Railway HTTP round trip: **4299.7 ms**

This established that removing rembg does not inherently destroy the V2 result. The browser migration problem is therefore primarily a porting/geometry problem rather than a requirement for hosted model inference.

## Real Chrome v0 benchmark

The actual JavaScript core was executed in Chrome on the same five cases.

| Case | JS ms | Shapes | JS vs proxy SSIM | JS vs proxy edge IoU | JS vs Railway SSIM |
| --- | ---: | ---: | ---: | ---: | ---: |
| Raden | 35.3 | 40 | 0.7249 | 0.0551 | 0.7085 |
| Subaru | 14.1 | 40 | 0.7351 | 0.0807 | 0.7338 |
| Noel | 13.9 | 40 | 0.7356 | 0.0642 | 0.7328 |
| Elizabeth | 9.2 | 40 | 0.7617 | 0.0991 | 0.7636 |
| Night River | 10.4 | 40 | 0.6475 | 0.1175 | 0.6474 |

Mean JavaScript results:

- processing: **16.6 ms**
- shape count: **40.0**
- JS vs Python unguided proxy SSIM: **0.7210**
- JS vs Python unguided proxy edge IoU: **0.0833**
- JS vs Railway SSIM: **0.7172**
- JS vs Railway edge IoU: **0.0825**

Machine-readable benchmark data is stored at `docs/benchmarks/browser_fallback_v0_20260930.json`.

## Review result

### Functional gate: PASS

- JavaScript syntax passes.
- Browser fallback contract tests pass.
- Existing V2 browser migration tests pass.
- Real Chrome completes the browser algorithm.
- No server-side Python is required.
- No external model runtime is required.
- Runtime cost is small enough that compute time is not the blocker.

### Quality gate: HOLD

The v0 output is not yet a suitable Railway replacement.

The first visible bad stage is **component -> polygon geometry**.

The current convex-hull conversion fills across concavities and can bridge unrelated parts of the same color component. This produces oversized triangular/polygonal slabs, weak silhouette fidelity, and very low edge IoU. The problem is especially visible in character limbs/hair and in complex scenic boundaries.

Do not compensate for this by tuning palette counts or merely raising `maxShapes`. That would treat the downstream symptom rather than the first bad stage.

## Next engineering step: Browser Fallback v1

v1 should replace convex-hull geometry with mask-faithful contour geometry while retaining the fast browser-only architecture.

Priority order:

1. trace the actual connected-component boundary instead of taking its convex hull;
2. simplify that traced contour with a fidelity guard;
3. introduce edge-aware splitting before geometry when one color cluster spans visibly separate structures;
4. move color distance toward the canonical Lab-based behavior;
5. add a small region-adjacency merge stage rather than global same-color geometry;
6. rerun the same five-case comparison before broadening the corpus.

The Python unguided proxy remains the migration target. Browser v1 should first approach that proxy before any attempt is made to remove Railway from the default route.

## Railway graduation rule

Do not remove Railway yet.

Railway graduation becomes eligible only after:

1. Local Worker remains the primary high-quality route;
2. Browser Fallback passes the fixed visual comparison set;
3. Browser fallback failure safely degrades without losing the uploaded image or UI state;
4. the production default can be switched with an immediate rollback path;
5. real browser smoke passes on desktop and mobile/Tailscale usage.

Until then, Browser Fallback stays an opt-in development route.
