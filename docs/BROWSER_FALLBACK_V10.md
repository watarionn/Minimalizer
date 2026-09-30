# Browser Fallback v10

Status: **SHARED-BOUNDARY CONTOUR PARITY PASS / EXACT QUALITY IMPROVED / LITE SPEED PRESERVED / RAILWAY GRADUATION HOLD**

Date: 2026-10-01  
Branch: `feature/browser-fallback-v10-contour-parity-20261001`

Production default remains unchanged. Browser fallback is still opt-in. Lite keeps the fast v9 contour route, while the Exact profile uses the new shared-boundary canonical contour route.

## Goal

v10 closes the next first-bad-stage after v9 canonical palette parity:

**contour simplification and raster geometry fidelity**

v9 had already aligned:

- source raster for the no-resize character cases;
- exact structural preprocessing;
- OpenCV-compatible Lab;
- canonical SLIC;
- Region Merge and hierarchy cut;
- palette medoids, hierarchy, assignments, and protected-relationship repair.

The remaining final-image gap was primarily geometric.

## First-bad-stage audit

Before implementing v10, Raden, Subaru, and Noel were measured at each Python downstream stage.

The Browser v9 exact image was compared with:

1. Python selected region labels rendered with canonical palette;
2. Python simplified contours;
3. Python selected primitives;
4. Python final scene without facets;
5. Python final scene with facets.

### Raden

Browser v9 vs Python selected labels:

- SSIM: **0.9065**
- edge IoU: **0.3456**

Browser v9 vs Python contour:

- SSIM: **0.9012**
- edge IoU: **0.2934**

Python contour to primitive:

- mean mask IoU: **1.0000**

### Subaru

Browser v9 vs Python selected labels:

- SSIM: **0.9542**
- edge IoU: **0.4196**

Browser v9 vs Python contour:

- SSIM: **0.9361**
- edge IoU: **0.3626**

Python contour to primitive:

- mean mask IoU: **0.9973**

### Noel

Browser v9 vs Python selected labels:

- SSIM: **0.9300**
- edge IoU: **0.4257**

Browser v9 vs Python contour:

- SSIM: **0.8997**
- edge IoU: **0.3130**

Python contour to primitive:

- mean mask IoU: **0.9975**

The major drop therefore occurs at contour simplification, while primitive fitting changes very little on these three cases.

## Rejected shortcut: epsilon-only tuning

The old Browser contour implementation simplified each region independently.

A small sweep increased simplification strength while lowering the local contour fidelity threshold.

This did not reliably move Browser output toward Python:

- Raden and Subaru generally became worse against the Python contour;
- Noel improved only marginally;
- shared region boundaries remained independently approximated.

The problem was not just simplification strength.

## Canonical shared-boundary contour

v10 adds:

`web/static/canonical-contour.js`

The module ports the relevant unguided Minimal contour contract into deterministic self-hosted JavaScript.

It implements:

- boundary segment extraction by canonical region pair;
- outside-image boundary handling;
- multi-region junction and border anchors;
- deterministic cycle anchors;
- pair-chain tracing;
- half-edge orientation;
- shared region-loop assembly;
- micro cleanup;
- open-chain Douglas-Peucker simplification;
- Minimal epsilon ratio `0.022`;
- epsilon clamp `0.75..18 px`;
- candidate factors `1.0, 0.75, 0.50, 0.25, 0.0`;
- region IoU, area, centroid, and directional guards;
- major-mass directional tightening;
- candidate-chain intersection checks;
- Minimal planar line fitting;
- connected-component and hole topology guards.

A single shared chain is simplified once and reused by both adjacent regions. This removes the independent-boundary drift that existed in v9.

The module has no network or model runtime dependency.

## Standalone Python contour parity

On the exact-upstream no-resize character cases, the raw shared-boundary vertex count matches Python exactly.

### Raden

- raw vertices: Python **6368**, Browser **6368**
- simplified vertices: Python **717**, Browser **703**
- Python contour vs Browser contour:
  - SSIM **0.9965**
  - edge IoU **0.9386**
  - RGB MAE **0.0830**

### Subaru

- raw vertices: Python **7049**, Browser **7049**
- simplified vertices: Python **1380**, Browser **1389**
- Python contour vs Browser contour:
  - SSIM **0.9917**
  - edge IoU **0.9130**
  - RGB MAE **0.2174**

Per-region Python/Browser contour mask comparison on Subaru:

- mean IoU: **0.9839**
- 10th percentile: **0.9548**
- worst IoU: **0.8500**
- exact region masks: **16 / 40**

### Noel

- raw vertices: Python **6920**, Browser **6920**
- simplified vertices: Python **1108**, Browser **898**
- Python contour vs Browser contour:
  - SSIM **0.9853**
  - edge IoU **0.8260**
  - RGB MAE **0.4100**

Noel therefore remains the largest contour residual among the three character probes.

## Profile split

The first integrated version applied shared-boundary contour to both Lite and Exact.

That raised Lite processing from roughly the v9 one-second class to roughly four seconds on representative character cases.

v10 therefore uses:

### Lite default

- structural profile: `l0-lite-jacobi`
- contour: `legacy-independent-rings`
- canonical palette: enabled

### Exact opt-in

- structural profile: `spectral-exact`
- contour: `canonical-shared-chain`
- canonical palette: enabled

The configuration flag `canonicalContourLite` defaults to false.

The canonical contour route remains available for controlled Lite experiments without making it the default.

## Lite stability

A real Chrome Raden Lite run was compared pixel-for-pixel with the v9 Lite artifact.

Result:

- pixel exact: **yes**
- changed pixel ratio: **0.0**
- RGB MAE: **0.0**
- contour method: `legacy-independent-rings`
- measured core processing: **1167.4 ms**

The Lite quality/speed contract is therefore preserved.

## Five-case Exact benchmark

Browser v10 Exact vs Python unguided proxy:

- mean SSIM: **0.9471**
- mean edge IoU: **0.4741**
- mean RGB MAE: **1.5682**
- mean processing time in this local Chrome run: **14058.1 ms**
- mean shared contour vertices: **984.4**

v9 Exact vs Python proxy:

- SSIM: **0.9065**
- edge IoU: **0.3353**
- RGB MAE: **2.8992**

The contour phase produces the largest Browser quality gain since the upstream parity work.

### Per-case Exact results

| Case | Proxy SSIM | Proxy edge IoU | Proxy MAE |
| --- | ---: | ---: | ---: |
| Raden | 0.9420 | 0.3999 | 0.8710 |
| Subaru | 0.9660 | 0.5703 | 0.9739 |
| Noel | 0.9529 | 0.4808 | 1.2707 |
| Elizabeth | 0.9482 | 0.5034 | 3.2610 |
| Night River | 0.9265 | 0.4161 | 1.4642 |

Historical edge-IoU improvements from v9 to v10 Exact:

- Raden: **0.2919 -> 0.3999**
- Subaru: **0.3562 -> 0.5703**
- Noel: **0.3159 -> 0.4808**
- Elizabeth: **0.3933 -> 0.5034**
- Night River: **0.3192 -> 0.4161**

## Railway comparison

Browser v10 Exact vs current Railway fallback:

- mean SSIM: **0.8795**
- mean edge IoU: **0.3240**
- mean RGB MAE: **10.5650**

For comparison, v9 Exact vs Railway was:

- SSIM: **0.8563**
- edge IoU: **0.2827**

The Browser route improves against Railway too, but this is not a Railway-parity claim.

The Python unguided proxy itself differs from Railway because Railway has rembg-guided V2 evidence.

Historical Python unguided proxy vs Railway:

- SSIM: **0.9067**
- edge IoU: **0.5332**

## Real wrapper smoke

A generated 100 x 78 PNG was processed through real Chrome `minimalizeFile()` at analysis side 40.

Lite reports:

- mode: `browser-fallback-v10`
- contour: `legacy-independent-rings`
- palette: `canonical-medoid-hierarchy`
- resize: `opencv-inter-area`

Exact reports:

- mode: `browser-fallback-v10`
- contour: `canonical-shared-chain`
- palette: `canonical-medoid-hierarchy`
- resize: `opencv-inter-area`
- minimum region contour IoU: **0.9661**

Contour method and minimum contour IoU are exposed through response headers and metadata.

## Validation

Focused Browser v10 / spectral / migration suite:

- **31 passed**

Final Browser / migration / Web / Local Worker regression:

- **80 passed**
- one existing Starlette/httpx deprecation warning

Additional validation:

- JavaScript syntax: PASS
- `git diff --check`: PASS
- real Chrome wrapper: PASS
- real Chrome Lite v9 pixel stability: PASS

The v10 test suite locks the Subaru shared-boundary contract:

- raw boundary vertex count equals Python;
- simplified vertex count within 2%;
- Browser minimum region IoU >= 0.90;
- Python/Browser per-region contour mean IoU >= 0.98;
- 10th percentile >= 0.95;
- worst region >= 0.84.

It also locks the profile split:

- Lite uses legacy fast contour by default;
- Exact uses canonical shared contour;
- canonical contour can be enabled experimentally for Lite.

## Gate

### First-bad-stage isolation: PASS

Contour simplification was independently identified before implementation.

### Shared raw boundary extraction: PASS

Raw boundary vertex count matches Python exactly on all three character probes.

### Shared contour parity: PASS

The Browser contour closely matches Python, with Subaru mean per-region IoU above 0.98.

### Lite stability: PASS

The real Raden Lite output is pixel-identical to v9.

### Exact quality: PASS

Five-case proxy SSIM and edge IoU improve substantially.

### Railway graduation: HOLD

Railway should not be removed yet.

## Remaining gaps

### Contour residuals

Shared contour is close but not byte-identical to Python.

Noel has the largest remaining contour residual.

The Browser implementation uses deterministic JavaScript Douglas-Peucker and topology logic, while Python uses OpenCV operations and high-resolution raster guards.

### Rasterization

Browser output is filled by Canvas.

Python V2 rasterizes geometry through a 2x mask path using OpenCV-compatible geometry operations.

Raster fill semantics are now a likely next first-bad-stage.

### Primitive and facet residuals

Primitive fitting was nearly identity on the three diagnostic character cases, but it is not guaranteed to be negligible on every image.

Facet overlays also introduce a small final-stage difference.

### Elizabeth decode residual

The known one-level Browser/OpenCV WebP decode residual remains.

### Exact runtime

The current Exact shared-contour route is quality-first and expensive.

The measured five-case local mean was about 14 seconds.

This number is environment-dependent, but the route needs optimization before Exact can become a general default.

### Large-image memory

The v8 native RGBA materialization caveat still applies.

Large-image memory guard or tiled area resize remains an operational prerequisite for Railway graduation.

## v11 target

The next recommended phase is:

**rasterization parity and contour residual closure**

Recommended sequence:

1. compare Browser and Python masks using identical final contour loops;
2. isolate Canvas fill differences from contour-coordinate differences;
3. reproduce the Python 2x raster sampling contract where beneficial;
4. audit the worst contour residuals, starting with Noel;
5. verify whether remaining primitive/facet differences are material after raster parity;
6. rerun the five-case Exact benchmark;
7. separately profile and optimize canonical contour runtime;
8. keep Lite unchanged unless optimization makes the shared route cheap enough.

Railway should remain available until raster parity, runtime, and Browser memory hardening are closed.
