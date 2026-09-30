# Browser Fallback v8

Status: **OPENCV INTER_AREA PARITY PASS / FULL BROWSER QUALITY IMPROVED / RAILWAY GRADUATION HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Browser fallback remains opt-in, lite remains its default profile, and exact spectral remains quality-first opt-in.

## Goal

v8 closes the analysis-resize mismatch isolated by v7.

Python V2 uses:

```text
source RGB
 -> cv2.resize(..., interpolation=cv2.INTER_AREA)
 -> analysis RGB
```

Browser v7 used Canvas `drawImage` for downscaling, which materially changed the analysis raster for inputs above 400 px.

v8 replaces that resize step with a deterministic JavaScript implementation of OpenCV's uint8 `INTER_AREA` path.

## New module

v8 adds:

`web/static/opencv-area-resize.js`

The module reproduces OpenCV's non-integer downscale path:

- OpenCV-compatible area contribution tables;
- float32 X coefficients;
- float32 Y coefficients;
- float32 horizontal accumulation;
- float32 vertical accumulation;
- OpenCV-compatible final uint8 rounding.

The module is static and self-hosted.

`index.html` loads it before `browser-fallback.js`.

## Browser input path

The Browser path now performs:

```text
decode
 -> native-size white alpha composite
 -> OpenCV-compatible INTER_AREA analysis resize
 -> Browser V2 pipeline
```

If no resize is needed, the route reports `native`.

If the compatibility module is unexpectedly unavailable, the Browser engine retains a Canvas resize fallback rather than failing the request.

The active resize path is exposed as:

- response header: `X-Minimalizer-Analysis-Resize`
- metadata: `analysisResize`

## Independent resize parity

Five deterministic random RGB fixtures were tested across several non-integer downscale ratios.

Browser `resizeRgba()` was compared byte-for-byte with:

```python
cv2.resize(rgb, (dest_width, dest_height), interpolation=cv2.INTER_AREA)
```

Result:

- exact fixtures: **5 / 5**
- maximum absolute channel error: **0**
- mean absolute channel error: **0**
- exact channel fraction: **1.0000**

The resize implementation itself is therefore exact on the tested uint8 domain.

## Real corpus analysis-raster parity

### Night River

Browser native decode is already exact to Python.

After v8 area resizing:

- analysis RGB exact: **yes**
- mean absolute error: **0.0**
- max absolute error: **0**
- exact pixels: **100%**

### Elizabeth

Browser WebP decode has a pre-existing one-level residual relative to OpenCV decode.

After v8 area resizing:

- mean absolute error: **0.00469**
- max absolute error: **1**
- exact pixels: **98.78%**
- exact channels: **99.53%**

For comparison, v7 Canvas resize produced:

- mean absolute error: **1.019**
- max absolute error: **70**
- exact pixels: **62.04%**

The v8 resize mismatch is therefore closed. The remaining Elizabeth difference originates in Browser vs OpenCV WebP decoding / alpha-color rounding, not the resize algorithm.

## Real Chrome exact preprocessing / SLIC parity

The full Browser-owned input path was tested:

```text
Browser decode
 -> native white composite
 -> v8 INTER_AREA resize
 -> exact spectral L0
 -> OpenCV-compatible Lab
 -> canonical edge
 -> canonical SLIC
```

Results:

| Case | Resize | Browser regions | Python regions | Exact label map |
| --- | --- | ---: | ---: | --- |
| Raden | native | 632 | 632 | yes |
| Subaru | native | 538 | 538 | yes |
| Noel | native | 788 | 788 | yes |
| Elizabeth | opencv-inter-area | 533 | 532 | no |
| Night River | opencv-inter-area | 769 | 769 | yes |

Four of five cases are exact from Browser-owned source decode through SLIC.

Elizabeth's one-region difference is caused by the remaining maximum-one-level WebP decode residual.

## Five-case Browser benchmark

### Lite default

v8 lite:

- processing: **858.7 ms**
- initial regions: **643.6**
- vertices: **1507.6**
- proxy SSIM: **0.8513**
- proxy edge IoU: **0.2636**
- Railway SSIM: **0.8354**
- Railway edge IoU: **0.2517**

v7 lite:

- proxy SSIM: **0.8453**
- proxy edge IoU: **0.2627**

Lite quality improves slightly while staying in roughly the same sub-second core-processing class.

### Exact opt-in

v8 exact:

- processing: **11454.1 ms**
- initial regions: **652.0**
- vertices: **1546.4**
- proxy SSIM: **0.8817**
- proxy edge IoU: **0.3069**
- Railway SSIM: **0.8533**
- Railway edge IoU: **0.2735**

v7 exact:

- proxy SSIM: **0.8598**
- proxy edge IoU: **0.2810**

The resize fix produces a substantial quality gain in exact mode.

Per-case highlights:

- Elizabeth exact proxy SSIM: **0.9111**
- Elizabeth exact proxy edge IoU: **0.3733**
- Night River exact proxy SSIM: **0.8439**
- Night River exact proxy edge IoU: **0.3099**

Exact remains too slow to become the default Browser profile.

## Real wrapper smoke

A generated 100 x 78 PNG was processed through real Chrome `minimalizeFile()` with `analysisMaxSide=40`.

Both profiles report:

- mode: `browser-fallback-v8`
- compute: Browser
- analysis resize: `opencv-inter-area`

Lite reports:

- structural profile: `l0-lite-jacobi`

Exact reports:

- structural profile: `spectral-exact`

Response headers and metadata agree.

## Validation

Final focused Browser / migration / Web / Local Worker regression:

- **77 passed**
- one existing Starlette/httpx deprecation warning
- JavaScript syntax: PASS
- `git diff --check`: PASS

The v8 test suite locks:

- OpenCV area resize parity;
- script load order;
- v8 version contract;
- resize header / metadata contract;
- inherited OpenCV Lab parity;
- inherited exact SLIC parity;
- inherited Region Merge parity.

## Gate

### OpenCV INTER_AREA compatibility: PASS

The deterministic Browser resize matches OpenCV exactly on the independent test fixtures.

### Real scaled corpus resize parity: PASS

Night River is exact.

Elizabeth is reduced to the pre-existing maximum-one-level decode residual.

### Canonical Lab: PASS

Inherited from v7.

### Canonical SLIC implementation: PASS

Inherited from v6.

### Region Merge / cut: PASS

Inherited from prior exact-parity phases.

### Full Browser quality: IMPROVED, still below graduation target

v8 exact closes a meaningful part of the quality gap, but the aggregate proxy baseline remains:

- Python unguided proxy vs Railway SSIM: **0.9067**
- Python unguided proxy vs Railway edge IoU: **0.5332**

Browser v8 exact reaches:

- proxy SSIM: **0.8817**
- proxy edge IoU: **0.3069**

### Railway graduation: HOLD

Railway remains the hosted escape hatch.

## Remaining gaps

### Small upstream residual

Elizabeth retains a maximum-one-level Browser/OpenCV WebP decode difference.

This is now small enough to isolate separately from algorithmic resize parity.

### Primary downstream quality gap

Raden, Subaru and Noel require no resize and already match through:

- source raster;
- exact structural preprocessing;
- canonical Lab;
- canonical SLIC;
- Region Merge / hierarchy cut.

Their final Browser results still differ from the Python proxy.

The next earliest downstream stage is therefore:

**palette selection / medoid fidelity**

Contour simplification remains after palette.

## Operational caveat

v8 prioritizes parity by materializing a native-size RGBA canvas before analysis resizing.

This is safe for the current fixed corpus, but very large uploads can consume substantial Browser memory.

Before Railway graduation, Browser fallback still needs either:

- a large-image memory guard; or
- a tiled native decode / area-resize path.

This is an operational hardening item rather than a v8 correctness blocker.

## v9 target

v9 should audit canonical palette fidelity on the three no-resize character cases first.

Recommended sequence:

1. compare Python and Browser selected palette RGB values on identical post-merge labels;
2. compare region-to-palette assignments;
3. compare medoid candidate ordering and tie rules;
4. compare relationship / accent protections;
5. require exact or near-exact palette parity before touching contour geometry;
6. rerun the five-case quality benchmark;
7. then move to contour simplification parity if the remaining gap is geometric.

The small Elizabeth decode residual and large-image Browser memory hardening remain tracked separately.

Railway should stay available until the downstream palette / contour gap is closed and public Browser memory behavior is hardened.
