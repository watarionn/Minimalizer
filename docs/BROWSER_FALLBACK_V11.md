# Browser Fallback v11

Status: **RASTER PARITY PASS / CONTOUR GUARD PARITY PASS / UNGUIDED PROXY NEAR-PARITY / LITE STABLE / RAILWAY GRADUATION HOLD**

Date: 2026-10-01  
Branch: `feature/browser-fallback-v11-raster-parity-20261001`

Production default remains unchanged. Browser fallback is still opt-in. Lite keeps the v9/v10 fast Canvas route. Exact now uses both the canonical shared-boundary contour path and a deterministic OpenCV-compatible 2x polygon raster path.

## Goal

v11 closes the two residuals isolated after v10:

1. Canvas polygon fill / overwrite behavior did not match Python V2 rasterization.
2. The canonical contour candidate guards still used Browser point-in-polygon masks while Python used the same OpenCV 2x raster contract as final geometry validation.

The target was not to tune output visually. The target was to make Browser Exact use the same discrete geometry contract as Python unguided V2.

## Raster first-bad-stage

Using identical Python contour loops, a Browser-style pixel-center even-odd raster was compared with Python `rasterize_loops(..., scale=2)`.

Even with identical loops, the simple point-center path changed about 0.4% of pixels on the three character probes and produced edge IoU around 0.73 to 0.76.

Therefore the residual was not only contour coordinates.

Python V2 rasterization uses:

- polygon coordinates rounded on a 2x lattice;
- non-antialiased 8-connected polygon edges;
- fixed-point active-edge scanline filling;
- inclusive boundary pixels;
- XOR composition across loops;
- sampling at the 2x center offset.

## Deterministic OpenCV-compatible raster

v11 adds:

`web/static/opencv-fill-raster.js`

The module implements the small deterministic subset needed by Minimalizer:

- 8-connected Bresenham edge rasterization;
- 16-bit fixed-point active-edge scan conversion;
- inclusive horizontal spans;
- polygon-loop XOR composition;
- 2x sampling;
- deterministic RGBA scene rendering;
- region-id ordered overwrite behavior.

It does not load OpenCV.js and has no network or model runtime dependency.

The compatibility behavior was derived and independently implemented against the public OpenCV polygon filling contract in `modules/imgproc/src/drawing.cpp`.

## Exact same-loop raster parity

The compatibility raster was first tested with the **same Python contour loops** before integration.

### Raden

- pixel exact: **yes**
- changed pixel ratio: **0.0**
- RGB MAE: **0.0**
- SSIM: **1.0**
- edge IoU: **1.0**

### Subaru

- pixel exact: **yes**
- changed pixel ratio: **0.0**
- RGB MAE: **0.0**
- SSIM: **1.0**
- edge IoU: **1.0**

### Noel

- pixel exact: **yes**
- changed pixel ratio: **0.0**
- RGB MAE: **0.0**
- SSIM: **1.0**
- edge IoU: **1.0**

This established that the Browser can reproduce the Python 2x mask contract exactly for the tested contour set.

## Renderer integration

Exact rendering now uses:

`canonical-shared-chain -> opencv-fillpoly-2x -> ImageData`

Region overwrite order is ascending region id, matching the Python geometry renderer contract for the normalized Browser region ordering.

Lite rendering remains:

`legacy-independent-rings -> canvas-evenodd`

This preserves the fast fallback contract.

New response metadata:

- `X-Minimalizer-Raster-Method`
- `metadata.rasterMethod`

Possible values:

- `canvas-evenodd`
- `opencv-fillpoly-2x`

## Canonical contour guard parity

v10 still validated contour candidates with Browser point-in-polygon masks.

v11 routes those candidate guards through the same OpenCV-compatible 2x raster.

This closes the previously observed fallback/rejection drift.

### Raden

Python:

- original vertices: **6368**
- simplified vertices: **717**
- fallback chains: **4**
- rejected candidates: **16**
- minimum region IoU: **0.9178082192**

Browser v11:

- original vertices: **6368**
- simplified vertices: **720**
- fallback chains: **4**
- rejected candidates: **16**
- minimum region IoU: **0.9178082192**

Python/Browser final contour masks:

- mean per-region IoU: **0.999195**
- 10th percentile: **0.999392**
- worst region: **0.988131**
- contour render SSIM: **0.998936**
- contour render edge IoU: **0.982678**

### Subaru

Python:

- original vertices: **7049**
- simplified vertices: **1380**
- fallback chains: **8**
- rejected candidates: **44**
- minimum region IoU: **0.9111111111**

Browser v11:

- original vertices: **7049**
- simplified vertices: **1378**
- fallback chains: **8**
- rejected candidates: **44**
- minimum region IoU: **0.9111111111**

Python/Browser final contour masks:

- mean per-region IoU: **0.998855**
- 10th percentile: **0.999107**
- worst region: **0.971467**
- contour render SSIM: **0.999020**
- contour render edge IoU: **0.985466**

### Noel

Python:

- original vertices: **6920**
- simplified vertices: **1108**
- fallback chains: **20**
- rejected candidates: **90**
- minimum region IoU: **0.9049977488**

Browser v11:

- original vertices: **6920**
- simplified vertices: **1109**
- fallback chains: **20**
- rejected candidates: **90**
- minimum region IoU: **0.9049977488**

Python/Browser final contour masks:

- mean per-region IoU: **0.999743**
- 10th percentile: **1.0**
- worst region: **0.991199**
- combined contour render: **pixel exact**
- SSIM: **1.0**
- edge IoU: **1.0**
- RGB MAE: **0.0**

The remaining 1 to 3 simplified-vertex difference on these probes is raster-invisible or nearly raster-invisible.

## Five-case Exact benchmark

Final v11 Exact vs Python unguided proxy:

- mean SSIM: **0.9913**
- mean edge IoU: **0.9113**
- mean RGB MAE: **0.6130**
- measured mean processing: **9656.4 ms**

v10 Exact vs Python proxy:

- SSIM: **0.9471**
- edge IoU: **0.4741**
- RGB MAE: **1.5682**

The raster and guard parity phase therefore removes most of the remaining implementation gap.

### Per-case final Exact results

| Case | Proxy SSIM | Proxy edge IoU | Proxy MAE |
| --- | ---: | ---: | ---: |
| Raden | 0.9983 | 0.9797 | 0.1075 |
| Subaru | 0.9973 | 0.9553 | 0.1906 |
| Noel | 0.9964 | 0.9638 | 0.3115 |
| Elizabeth | 0.9730 | 0.7570 | 2.1308 |
| Night River | 0.9914 | 0.9005 | 0.3249 |

The three no-resize character cases are now very close to the Python unguided proxy.

Elizabeth remains the clear outlier and retains the known Browser/WebP decode and resized-input residual.

## Railway comparison

Final v11 Exact vs current Railway fallback:

- mean SSIM: **0.9052**
- mean edge IoU: **0.5216**
- mean RGB MAE: **10.1017**

Historical Python unguided proxy vs Railway:

- SSIM: **0.9067**
- edge IoU: **0.5332**

The Browser v11 / Railway relationship is now close to the Python unguided-proxy / Railway relationship.

This is an important architecture milestone:

**the dominant remaining Railway difference is no longer the Browser port itself.**

It is primarily the semantic evidence difference between:

- Railway: rembg-guided V2;
- Browser Exact: unguided V2-compatible path.

## Lite stability

A real Chrome Raden Lite run was compared pixel-for-pixel with the v9 Lite artifact.

Result:

- version: `browser-fallback-v11`
- contour: `legacy-independent-rings`
- raster: `canvas-evenodd`
- measured processing: **1192.7 ms**
- pixel exact: **yes**
- changed pixel ratio: **0.0**
- RGB MAE: **0.0**

The Lite speed/quality contract remains unchanged.

## Real wrapper smoke

A generated 100 x 78 PNG was processed through real Chrome `minimalizeFile()`.

Lite reports:

- mode: `browser-fallback-v11`
- contour: `legacy-independent-rings`
- raster: `canvas-evenodd`
- palette: `canonical-medoid-hierarchy`
- resize: `opencv-inter-area`

Exact reports:

- mode: `browser-fallback-v11`
- contour: `canonical-shared-chain`
- raster: `opencv-fillpoly-2x`
- palette: `canonical-medoid-hierarchy`
- resize: `opencv-inter-area`

Response headers and metadata agree on the raster method.

## Validation

Focused Browser v11 / spectral / migration suite:

- **33 passed**

Final Browser / migration / Web / Local Worker regression:

- **82 passed**
- one existing Starlette/httpx deprecation warning

Additional validation:

- JavaScript syntax: PASS
- OpenCV-compatible synthetic 2x raster fixture: pixel exact
- real Chrome wrapper: PASS
- real Chrome Raden Lite stability: pixel exact
- five-case real Chrome Exact benchmark: PASS

The v11 test suite now locks:

- OpenCV-compatible raster equality against Python `rasterize_loops`;
- raster module load order before canonical contour;
- explicit Exact and Lite raster methods;
- Subaru original vertex count equality;
- simplified vertex difference <= 3;
- fallback chain count equality;
- rejected candidate count equality;
- minimum region IoU equality;
- Python/Browser contour mean region IoU >= 0.998;
- 10th percentile >= 0.9985;
- worst region >= 0.97.

## Gate

### Same-loop raster parity: PASS

The tested exact contour masks are pixel-identical.

### Contour candidate guard parity: PASS

Fallback/rejection decisions match Python on the primary Subaru regression and all three diagnostic character probes.

### Contour residual closure: PASS

The three no-resize character probes are effectively at raster parity.

### Unguided Python proxy parity: PASS

Five-case Exact reaches SSIM 0.9913 and edge IoU 0.9113 against the unguided proxy.

### Lite stability: PASS

Lite remains pixel-identical to v9 on the Raden stability probe.

### Railway graduation: HOLD

The implementation-parity phase is largely closed, but operational and semantic prerequisites remain.

## Remaining Railway-graduation prerequisites

### Semantic guidance gap

Railway still has rembg subject evidence.

Browser Exact is intentionally unguided.

Now that Browser/Python implementation parity is high, the remaining value of Railway should be evaluated as a semantic-guidance question rather than as a JavaScript-port question.

### Elizabeth decode / resize residual

The WebP / resized-input residual remains the most visible Browser-vs-proxy outlier.

### Exact runtime

The final local five-case mean was about 9.66 seconds.

This run is materially faster than the v10 measurement, but browser execution time varies enough that this should not be treated as a guaranteed speedup.

### Large-image memory

Native full-resolution RGBA materialization remains a memory concern before Browser fallback can be treated as production-safe for arbitrary large uploads.

### Production routing

The current production route still retains Railway.

Removing Railway requires an explicit deployment/routing phase for the Shin Free Server frontend and owner Local Worker path.

## Recommended v12 target

The next phase should stop treating Python-to-JavaScript parity as the main problem.

Recommended v12:

**Railway Graduation Prerequisites**

1. measure the semantic value of rembg guidance on a broader representative corpus;
2. decide whether Browser fallback needs analytical browser-side subject segmentation or whether unguided Exact is sufficient as last-resort fallback;
3. close the Elizabeth WebP / resize residual;
4. implement large-image memory guard or tiled preprocessing;
5. profile Exact runtime separately from quality;
6. prepare the Shin Free Server deployment/routing plan without changing production default yet.

Railway should remain available until those graduation gates are explicitly closed.
