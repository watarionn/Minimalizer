# Browser Fallback v1

Status: **FUNCTIONAL PASS / GEOMETRY PASS / QUALITY HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Railway remains the hosted fallback.

## Purpose

v1 addresses the first-bad-stage identified in Browser Fallback v0: convex-hull geometry that overfilled concave masks and crossed visible character boundaries.

The production architecture target remains:

```text
Local Worker
  -> Browser Fallback
  -> Railway (temporary escape hatch)
```

Railway is not eligible for removal yet.

## v1 changes

### Mask-faithful contour geometry

v0 converted each connected component to a convex hull. v1 instead:

1. emits oriented boundary edges from the actual component mask;
2. stitches those edges into one or more deterministic rings;
3. simplifies each ring;
4. measures the simplified raster against the original component;
5. reduces simplification epsilon until the contour fidelity gate passes;
6. renders multiple rings with the even-odd fill rule.

The default contour fidelity floor is `0.94`.

### True Region Adjacency Graph budget merge

v0 and the first v1 prototype rewrote palette labels to reduce shape count. That could create new disconnected components and did not guarantee the requested budget.

The final v1 implementation merges **component groups**, not labels.

- adjacency is measured from shared 4-neighbor boundaries;
- the smallest active component is merged first;
- adjacent targets prefer longest shared boundary, then larger area, then closer color;
- isolated components fall back to closest-color / closest-spatial group;
- geometry stays as separate rings when disconnected pixels share one final shape;
- active group count decreases exactly once per merge.

The fixed five-case benchmark now produces exactly **40 shapes for every case**.

## Validation

Synthetic gates:

- deterministic replay;
- concave-mask fidelity without convex hull;
- region-budget convergence without dropping covered pixels;
- no external network/model runtime;
- Browser Fallback stays opt-in;
- Railway stays the default hosted route.

Focused synthetic + migration suite: **10 passed**.

## Real Chrome benchmark

Five fixed cases were executed in Chrome.

| Case | JS ms | Shapes | Contour IoU | Budget merges | vs proxy SSIM | vs proxy edge IoU |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raden | 62.3 | 40 | 0.9910 | 459 | 0.6831 | 0.0609 |
| Subaru | 24.7 | 40 | 0.9881 | 108 | 0.7701 | 0.1203 |
| Noel | 136.1 | 40 | 0.9954 | 1742 | 0.7294 | 0.0732 |
| Elizabeth | 22.1 | 40 | 0.9959 | 185 | 0.7590 | 0.1204 |
| Night River | 31.3 | 40 | 0.9943 | 208 | 0.6581 | 0.1118 |

Mean:

- processing: **55.3 ms**
- shape count: **40.0**
- contour IoU: **0.9929**
- JS vs Python unguided proxy SSIM: **0.7199**
- JS vs Python unguided proxy edge IoU: **0.0973**
- JS vs Railway SSIM: **0.7184**
- JS vs Railway edge IoU: **0.0941**

Compared with v0:

- proxy SSIM: `0.7210 -> 0.7199`
- proxy edge IoU: `0.0833 -> 0.0973`

Geometry fidelity improved substantially, but total-image similarity did not.

Machine-readable results are stored in `docs/benchmarks/browser_fallback_v1_20260930.json`.

## Review result

### Functional gate: PASS

Browser-only processing works, remains deterministic, has no external model runtime, and stays fast enough for fallback use.

### Geometry gate: PASS

The original v0 failure is closed.

- convex hull is removed;
- mean contour IoU is 0.9929;
- visible giant hull slabs are gone;
- all five benchmark cases satisfy the 40-shape budget.

### Railway replacement quality: HOLD

v1 is still not a suitable replacement for the Python unguided proxy or Railway.

The new first-bad-stage is:

**pixel palette assignment -> spatial region formation**

The global pixel palette creates many disconnected islands before the shape budget stage. Examples:

- Raden needs 459 component-group merges;
- Noel needs 1742 merges;
- one final shape can contain many spatially unrelated rings;
- fine disconnected islands survive even though each individual ring has excellent mask fidelity.

This explains why contour IoU can be near 1.0 while full-image edge IoU remains low.

## Browser Fallback v2 target

Do not tune contour fidelity further. The geometry stage is no longer the root cause.

v2 should replace the global pixel-first segmentation with spatially coherent regions.

Priority:

1. spatial over-segmentation before palette assignment;
2. region-level representative color instead of raw-pixel global labels;
3. edge-aware adjacency merge;
4. Lab-like color distance at the region level;
5. prevent one final shape from collecting unrelated distant rings unless explicitly justified;
6. preserve the v1 mask-faithful contour renderer unchanged where possible.

The migration target remains the Python unguided V2 proxy. Railway graduation should not be reconsidered until the browser path closes the large gap to that proxy.
