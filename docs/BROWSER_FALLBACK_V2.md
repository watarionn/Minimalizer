# Browser Fallback v2

Status: **FUNCTIONAL PASS / SPATIAL PASS / QUALITY HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Railway remains the hosted fallback.

## Goal

v2 replaces the v1 pixel-first segmentation path with spatially coherent regions.

The target architecture remains:

```text
Local Worker
  -> Browser Fallback
  -> Railway (temporary escape hatch)
```

Railway is not removed in this phase.

## Why v2 was needed

v1 fixed convex-hull geometry, but one final shape could still collect many disconnected color islands.

The first bad stage was:

```text
pixel palette assignment -> spatial region formation
```

v2 changes the order to:

```text
pixel
  -> Lab + structural edge
  -> SLICO-lite spatial over-segmentation
  -> adaptive retry
  -> spatial RAG merge
  -> 40 shapes
  -> 8-color palette
  -> v1 mask-faithful contour renderer
```

## SLICO-lite

Browser v2 ports the important structure of the canonical Python V2 segmenter:

- CIELAB color space;
- regular spatial centers;
- move initial centers toward local low-edge pixels;
- local color + spatial distance;
- adaptive per-cluster color scale;
- deterministic iterations;
- split disconnected labels into 4-connected regions.

The measured runtime profile is:

- analysis max side: `400`;
- work max side: `400`;
- SLIC iterations: `10`;
- target superpixels: canonical `400..1200` rule;
- minimum average superpixel area: `64`;
- final shapes: `40`;
- palette target: `8`.

## Adaptive retry

v2 ports the canonical retry rule.

When structural edge coverage is below `0.75`:

1. reduce region size to `80%`;
2. rerun SLICO-lite;
3. accept only when edge coverage improves;
4. reject pathological region explosion above the configured `2.5x` target bound.

On the fixed five-case benchmark, 3 / 5 cases used the retry path.

## Spatial RAG merge

Regions are merged as connected spatial groups rather than global color labels.

Merge evidence includes:

- Lab color difference;
- shared boundary length;
- structural edge strength;
- topology / shared-boundary ratio;
- major-mass protection;
- small redundant-region reward.

The v1 contour renderer is retained after the region stage.

## Minimal palette alignment

Canonical Python V2 Minimal mode uses a target range of 6 to 9 palette colors.

Browser v2 currently uses a measured fixed target of 8 colors while the migration work continues.

The five-case Python proxy average is 7.6 colors, so the Browser target is inside the canonical range.

## Runtime-profile sweep

### 192 px / 6 iterations

- mean processing: **76.2 ms**
- mean initial regions: **447.0**
- mean proxy SSIM: **0.7841**
- mean proxy edge IoU: **0.1266**

### 256 px / 8 iterations

- mean processing: **124.1 ms**
- mean initial regions: **465.6**
- mean proxy SSIM: **0.8027**
- mean proxy edge IoU: **0.1522**
- mean vertices: **998.2**

### Final profile: 400 px / 10 iterations + adaptive retry

- mean processing: **336.5 ms**
- mean initial regions: **647.2**
- mean initial regions before retry: **542.4**
- retry count: **3 / 5**
- mean edge coverage: **0.7219**
- mean shapes: **40.0**
- mean palette count: **8.0**
- mean vertices: **1058.8**
- Browser v2 vs Python unguided proxy SSIM: **0.8364**
- Browser v2 vs Python unguided proxy edge IoU: **0.2188**
- Browser v2 vs Railway SSIM: **0.8444**
- Browser v2 vs Railway edge IoU: **0.2256**

Machine-readable results are stored at:

`docs/benchmarks/browser_fallback_v2_20260930.json`

## Alignment with canonical Python V2

The five-case Python unguided proxy averages:

- initial regions: **670.6**
- selected regions: **40.0**
- palette count: **7.6**
- simplified vertices: **1000.8**
- visible shapes: **40.0**

Browser v2 now averages:

- initial regions: **647.2**
- shapes: **40.0**
- palette count: **8.0**
- vertices: **1058.8**

This means segmentation density, shape budget, palette size, and contour complexity are now in the same neighborhood as the canonical Python path.

## Improvement across Browser versions

| Version | Proxy SSIM | Proxy edge IoU |
| --- | ---: | ---: |
| v0 | 0.7210 | 0.0833 |
| v1 | 0.7199 | 0.0973 |
| v2 192px | 0.7841 | 0.1266 |
| v2 256px | 0.8027 | 0.1522 |
| v2 final | **0.8364** | **0.2188** |

The Python unguided proxy versus Railway baseline remains:

- SSIM: **0.9067**
- edge IoU: **0.5332**

v2 therefore closes a large part of the browser gap, but not enough to graduate Railway.

## Large-map incident

During 400px Night River validation, Browser v2 initially failed before result generation.

Cause:

`Math.max(...labels)` expanded more than 124,000 label values as JavaScript function arguments and exceeded the argument stack.

Fix:

- replaced argument spread with a linear max-label scan;
- added a 400 x 311 large-region-map regression test.

After the fix, Night River completed at 400px with:

- 746 initial regions;
- adaptive retry enabled;
- 40 shapes;
- palette 8;
- 1353 vertices.

## Validation

Final focused gate:

- JavaScript syntax: PASS
- `git diff --check`: PASS
- Browser v2 / migration / web / Local Worker focused suite: **62 passed**
- 400px large-map regression: PASS
- real Chrome five-case core execution: PASS
- real Chrome `File -> minimalizeFile() -> PNG Response` smoke: PASS

The wrapper smoke returned:

- mode: `browser-fallback-v2`
- compute: `browser`
- 40 shapes
- palette 8
- adaptive SLIC metadata

## Gate result

### Functional: PASS

Browser v2 is a real serverless fallback implementation.

### Spatial over-segmentation: PASS

The v1 disconnected-island failure is closed.

### Runtime profile: PASS

400px / 10 iterations remains comfortably sub-second on the tested machine.

### Railway replacement quality: HOLD

The next first-bad-stage is now:

**Region Merge hierarchy / merge-cost fidelity**

Browser segmentation statistics are already close to Python V2, but the final selected boundaries still differ substantially.

The browser path currently approximates the canonical merge cost and does not yet reproduce all of:

- canonical color SSE cost;
- boundary histogram quantiles;
- geometry / hull-inflation cost;
- safe consolidation;
- full merge hierarchy;
- canonical hierarchy cut;
- palette medoid / relationship protections.

These are now more important than further SLIC or contour tuning.

## Browser Fallback v3 target

Do not retune SLIC density or contour fidelity first.

v3 should move the Browser merge stage toward canonical V2:

1. port canonical color-cost math;
2. replace mean-boundary evidence with boundary histograms / quantiles;
3. add geometry inflation protection;
4. port safe consolidation behavior;
5. record a deterministic merge hierarchy;
6. cut the hierarchy to the Minimal 40-region target;
7. only then revisit palette medoid details.

Railway graduation remains HOLD until that merge-stage gap is materially reduced.
