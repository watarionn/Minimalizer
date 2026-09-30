# Browser Fallback v7

Status: **OPENCV LAB PARITY PASS / SLIC PARITY PASS / RAILWAY GRADUATION HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**. Lite remains the normal Browser fallback and exact spectral remains opt-in.

## Goal

v7 closes the RGB -> Lab mismatch discovered after v6 reached exact SLIC parity on identical structural inputs.

Python V2 uses:

```text
uint8 RGB
 -> float32 RGB / 255
 -> cv2.cvtColor(..., COLOR_RGB2LAB)
```

OpenCV's default float RGB-to-Lab path is not merely the analytic CIELAB formula. It uses a quantized 33 x 33 x 33 RGB-to-Lab table and integer trilinear interpolation.

Browser v6 still used a direct analytic sRGB / XYZ / Lab conversion.

## OpenCV Lab compatibility module

v7 adds:

`web/static/opencv-lab-lut.js`

The module contains the canonical OpenCV 33^3 Lab node table generated once from the same installed OpenCV conversion used by Python V2.

Runtime conversion reproduces OpenCV's:

- `LAB_BASE = 16384` input quantization;
- 33^3 grid;
- 4-bit trilinear fractions;
- eight-corner integer weights;
- integer descale;
- float32 output scaling.

The module is static and self-hosted. There is no API or runtime server dependency.

`index.html` loads it before `browser-fallback.js`.

If the compatibility module is unavailable, Browser fallback retains the previous analytic Lab formula as a defensive standalone fallback.

## 100,000-color parity

The Browser LUT conversion was compared against Python:

```python
cv2.cvtColor(rgb.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
```

The fixture included 100,000 RGB colors and all 256 grayscale levels.

Result:

- L max error: **0.0**
- a max error: **0.0**
- b max error: **0.0**
- mean error: **0.0**
- exact rows: **100%**

This is exact float32 parity for the tested uint8 RGB domain.

## Full preprocessing parity from identical analysis pixels

For the fixed five cases, the same Python analysis RGBA bytes were passed into Browser:

```text
analysis RGBA
 -> exact spectral L0
 -> OpenCV-compatible Lab
 -> canonical Lab edge
 -> canonical SLIC
```

Result:

- structural Lab max absolute error: **0.0**
- structural Lab mean absolute error: **0.0**
- SLIC label pixel equality: **1.0000**
- exact label maps: **5 / 5**

Therefore the preprocessing path from analysis pixels through SLIC is canonical when the input raster is identical.

## Real Chrome parity without resize

Raden, Subaru and Noel are already 340 x 340 and do not enter the 400px resize path.

Their Browser-decoded source pixels match Python `load_image()` exactly.

Real Chrome exact-mode SLIC label hashes also match Python for all three cases.

The pure spectral L0 internal uint8 raster can differ by tiny floating-engine rounding between Chrome and NumPy, but after canonical Lab quantization the SLIC result remains identical.

## Source decode and resize isolation

Python production input uses OpenCV `imdecode`, composites alpha onto white, and uses `cv2.INTER_AREA` for analysis resizing.

### Native decode

- Night River native decode: **exact**
- Elizabeth native decode:
  - mean absolute difference: **0.00445**
  - maximum difference: **1**
  - exact pixels: **99.21%**

The remaining Elizabeth native difference is negligible one-level alpha/color rounding.

### Analysis resize

The three 340px character images remain exact because no resize is required.

The two larger cases differ after analysis resizing:

- Elizabeth:
  - mean abs: **1.019**
  - max abs: **70**
  - exact pixels: **62.04%**
- Night River:
  - mean abs: **2.004**
  - max abs: **63**
  - exact pixels: **28.60%**

This isolates the next upstream first-bad-stage to:

**Canvas `drawImage` resizing vs Python `cv2.INTER_AREA`**

## Five-case Browser benchmarks

### Lite default

- processing: **802.9 ms**
- initial regions: **638.6**
- vertices: **1459.0**
- proxy SSIM: **0.8453**
- proxy edge IoU: **0.2627**
- Railway SSIM: **0.8385**
- Railway edge IoU: **0.2557**

Compared with v4 lite:

- v4 SSIM: 0.8517
- v4 edge IoU: 0.2592

Canonical Lab improves edge alignment slightly, while SSIM moves slightly down.

### Exact opt-in

- processing: **8772.2 ms**
- initial regions: **646.8**
- vertices: **1553.0**
- proxy SSIM: **0.8598**
- proxy edge IoU: **0.2810**
- Railway SSIM: **0.8401**
- Railway edge IoU: **0.2602**

Compared with v5 exact:

- v5 SSIM: 0.8622
- v5 edge IoU: 0.2749

Canonical Lab again increases edge overlap while overall SSIM remains approximately flat.

## Wrapper smoke

Real Chrome `minimalizeFile()` passed for both Browser profiles.

Lite:

- mode: `browser-fallback-v7`
- compute: `browser`
- structural: `l0-lite-jacobi`
- palette: `8`

Exact:

- mode: `browser-fallback-v7`
- compute: `browser`
- structural: `spectral-exact`
- palette: `8`

For the 64 x 64 smoke fixture, the Minimal hierarchy target range correctly selects 24 shapes rather than forcing 40.

## Validation

Final focused Browser / migration / Web / Local Worker regression:

- **76 passed**
- JavaScript syntax: PASS
- `git diff --check`: PASS

## Gate

### OpenCV Lab compatibility: PASS

100,000 tested colors are exactly equal to the Python OpenCV float path.

### Canonical SLIC: PASS

Inherited from v6 and verified end-to-end from identical analysis pixels.

### Region Merge: PASS

Inherited from v3 exact parity work.

### Full Browser quality: HOLD

Canonical correctness improved, but the five-case full route remains materially below the Python proxy baseline.

### Railway graduation: HOLD

The Python unguided proxy vs Railway baseline remains:

- SSIM: **0.9067**
- edge IoU: **0.5332**

## Remaining first-bad-stages

There are now two clearly separated remaining gaps.

### Upstream, for images larger than 400px

**analysis resize parity**

Browser uses Canvas `drawImage`; Python uses `cv2.INTER_AREA`.

This is the earliest remaining mismatch for Elizabeth and Night River and should be fixed first.

### Downstream, including images that require no resize

Raden, Subaru and Noel already have source/decode/preprocess/SLIC parity, yet their final Browser render still differs from the Python proxy.

After the exact Region Merge/cut contract, the next downstream stages to audit are:

1. palette selection / medoid and relationship protections;
2. contour simplification and raster rendering.

Palette fidelity comes first in the pipeline and should be audited before contour tuning.

## v8 target

v8 should prioritize analysis resize parity:

1. implement deterministic `INTER_AREA`-equivalent RGB resizing in Browser;
2. preserve white alpha-composite semantics;
3. compare analysis RGB byte-for-byte on the two scaled corpus cases;
4. rerun exact preprocessing/SLIC parity after Browser-owned resize;
5. rerun five-case end-to-end quality.

Once resize parity is closed, audit canonical palette selection on the three no-resize character cases before changing contour geometry.

Railway remains the hosted escape hatch until these remaining full-route gaps are closed.
