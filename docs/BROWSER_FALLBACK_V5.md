# Browser Fallback v5

Status: **EXACT SPECTRAL MODE ADOPTED AS OPT-IN / LITE REMAINS DEFAULT / RAILWAY GRADUATION HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**.

## Goal

v5 evaluates whether the Browser fallback can reproduce the canonical Python L0 structural preprocessing more faithfully without requiring Railway or the Local Worker.

v4 already established that:

- Region Merge parity is exact on identical canonical inputs.
- Browser SLIC is already close to Python when given the same structural Lab and structural edge.
- The dominant remaining upstream mismatch is structural preprocessing.

v5 therefore targets the exact spectral L0 solve.

## Architecture

v5 adds a self-hosted pure JavaScript FFT module:

`web/static/spectral-fft.js`

The implementation includes:

- radix-2 FFT for power-of-two sizes;
- Bluestein FFT for arbitrary sizes;
- arbitrary-size 2D FFT;
- inverse transforms;
- exact spectral L0 structural smoothing matching the Python formulation.

This avoids requiring an external runtime dependency or a new server component.

The Browser engine now supports two structural profiles.

### Lite

```text
analysis RGB
 -> L0-lite Jacobi
 -> structural Lab
 -> structural edge
 -> SLIC
 -> canonical Region Merge
```

### Exact

```text
analysis RGB
 -> exact spectral L0
 -> structural Lab
 -> structural edge
 -> SLIC
 -> canonical Region Merge
```

## Browser quality selection

The normal Browser fallback remains on the lite profile.

Exact mode is opt-in and persisted through localStorage.

Enable exact:

```text
?browserFallbackQuality=exact
```

Return to lite:

```text
?browserFallbackQuality=lite
```

Browser fallback routing itself remains separately controlled through the existing `browserFallback` parameter.

## FFT correctness

The spectral module is tested independently before Browser integration.

### 1D

Prime and composite lengths were compared with a direct DFT.

Maximum error gate:

```text
< 1e-9
```

PASS.

### 2D

Arbitrary 7 x 5 transform roundtrip:

```text
FFT2 -> IFFT2
```

Maximum error:

```text
< 1e-9
```

PASS.

### Exact L0

A non-power-of-two 13 x 11 RGB fixture was compared against Python `l0_gradient_smooth()`.

Gate:

- maximum channel difference <= 1;
- mean channel difference <= 0.05.

PASS.

## Spectral-only runtime

The exact spectral structural step alone was measured before full pipeline integration.

- Raden 340 x 340: **6055.9 ms**
- Night River 400 x 311: **6420.8 ms**

This immediately established that pure JS exact spectral processing is substantially heavier than v4 L0-lite.

## Full Browser exact benchmark

Five fixed cases were run through:

```text
File
 -> exact spectral L0
 -> structural Lab / edge
 -> SLIC
 -> canonical Region Merge
 -> 40-region Minimal cut
 -> palette 8
 -> contour
 -> PNG
```

Final mean:

- processing: **9646.5 ms**
- initial regions: **644.2**
- selected regions: **40**
- palette: **8**
- vertices: **1485.4**
- vs Python unguided proxy SSIM: **0.8622**
- vs Python unguided proxy edge IoU: **0.2749**
- vs Railway SSIM: **0.8407**
- vs Railway edge IoU: **0.2549**

## Comparison with v4

v4 lite:

- processing: **851.0 ms**
- proxy SSIM: **0.8517**
- proxy edge IoU: **0.2592**
- vertices: **1472.4**

v5 exact:

- processing: **9646.5 ms**
- proxy SSIM: **0.8622**
- proxy edge IoU: **0.2749**
- vertices: **1485.4**

Exact spectral therefore improves both image similarity and edge overlap, but at roughly an order-of-magnitude runtime cost.

The quality gain is real but not large enough to justify replacing the lite profile as the default Browser fallback.

## Why exact remains opt-in

The project goal is Railway graduation, not merely mathematical parity in one internal stage.

The Python unguided proxy versus Railway reference remains:

- SSIM: **0.9067**
- edge IoU: **0.5332**

v5 exact reaches:

- SSIM: **0.8622**
- edge IoU: **0.2749**

The Browser route therefore still leaves a substantial end-to-end quality gap even after exact L0 preprocessing.

Promoting exact spectral to the normal Browser fallback would impose about 10 seconds of core processing while still not closing enough of the remaining quality gap.

Decision:

- exact spectral implementation: **adopt**
- exact spectral default: **do not promote**
- exact spectral quality mode: **adopt as opt-in**
- v4 L0-lite default: **keep**
- Railway graduation: **hold**

## Exact wrapper smoke

Real Chrome `minimalizeFile()` exact mode passed.

Observed response:

- mode: `browser-fallback-v5`
- compute: `browser`
- structural preprocess: `spectral-exact`
- Jacobi iterations: `0`
- shapes: `40`
- palette: `8`
- hierarchy cut: `40`

The structural profile is exposed in both response headers and Browser metadata.

## Remaining gap

The next isolation target is no longer L0.

When Browser SLIC receives the exact Python structural inputs:

- mean boundary IoU: **0.9447**
- Browser -> Python region purity: **0.9916**
- Python -> Browser region purity: **0.9916**

That is already close, but not exact.

With v5 exact spectral, the structural preprocessing mismatch is largely removed, so the next first-bad-stage is:

**canonical SLIC parity**

The current Browser SLIC implementation still differs slightly in floating-point accumulation, center updates, assignment order, and disconnected-label output relative to the Python NumPy implementation.

Those small partition changes propagate through a deterministic Region Merge tree and alter the final visual result.

## Secondary remaining candidate

Contour complexity also remains higher than Python:

- Python unguided mean vertices: **1000.8**
- v5 exact mean vertices: **1485.4**

Therefore contour simplification and palette fidelity remain the next downstream candidates if exact SLIC parity does not close the gap enough.

## Validation

Focused Browser v5 + spectral tests:

- **20 passed**

Full Browser / migration / Web / Local Worker regression before final documentation:

- **72 passed**
- JavaScript syntax: PASS
- `git diff --check`: PASS

v5 spectral tests lock:

- prime/composite FFT correctness;
- arbitrary-size FFT2 roundtrip;
- exact L0 parity;
- exact profile metadata;
- Browser quality-profile URL contract;
- v3 canonical Region Merge parity inherited by the Browser v5 suite.

## v6 target

Do not optimize exact spectral runtime first.

The spectral implementation has already answered its research question.

v6 should focus on canonical SLIC parity:

1. compare Browser and Python center initialization exactly;
2. compare center movement to low-edge pixels;
3. compare floating-point precision and accumulation order;
4. match per-cluster color-scale update order;
5. match assignment tie behavior;
6. match connectivity splitting order;
7. require near-exact label-boundary parity before changing contour or palette;
8. rerun the five-case end-to-end benchmark with v5 exact structural input.

If SLIC parity does not materially close the final output gap, move next to contour simplification parity.

Railway remains available until the Browser route closes enough of the full-pipeline gap.
