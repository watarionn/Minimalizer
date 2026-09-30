# Browser Fallback v6

Status: **CANONICAL SLIC PARITY PASS / FULL BROWSER QUALITY MIXED / RAILWAY GRADUATION HOLD**

Date: 2026-09-30
Branch: `feature/browser-fallback-v0-20260930`
Production default: **unchanged**.

## Goal

v6 closes the remaining implementation gap between Browser SLICO-lite and the canonical Python NumPy SLICO implementation.

v5 had already shown that Browser SLIC was close when given identical Python structural inputs:

- boundary IoU: 0.9447
- region purity: about 0.9916

The remaining differences were small enough to point to numerical precision and component ordering rather than algorithm structure.

## Root cause

Two concrete differences were found.

### 1. SLIC distance precision

Python uses float64 for:

- distance buffers;
- color scales;
- center arithmetic.

Browser used:

- Float32Array for the distance buffer;
- Float32Array for color scales.

Those float32 roundings were enough to change pixels near cluster decision boundaries.

v6 changes both buffers to Float64Array.

### 2. Connectivity component numbering

Python `split_disconnected_labels()` assigns final region IDs in:

1. ascending source-label order;
2. connected-component raster order within each source label.

Browser previously assigned IDs by scanning all pixels globally.

That changed raw region IDs even when the geometric partition was the same.

v6 now reproduces the Python source-label-first ordering.

## Canonical SLIC parity

Five fixed cases were run with exactly the same Python:

- structural Lab;
- structural edge.

Python used `_run_numpy_slico() -> split_disconnected_labels()`.

Browser used `runSlicoLite()`.

Result after the v6 fixes:

| Case | Python regions | Browser regions | Exact label map |
| --- | ---: | ---: | --- |
| Raden | 629 | 629 | yes |
| Subaru | 538 | 538 | yes |
| Noel | 790 | 790 | yes |
| Elizabeth | 627 | 627 | yes |
| Night River | 769 | 769 | yes |

Aggregate:

- boundary IoU: **1.0000**
- Browser -> Python purity: **1.0000**
- Python -> Browser purity: **1.0000**
- pixel label equality: **1.0000**
- exact label maps: **5 / 5**

This closes canonical SLIC implementation parity.

## Automated parity gate

v6 adds a direct cross-language test.

A deterministic 31 x 29 Lab/edge fixture is passed to:

Python:

```text
_run_numpy_slico()
 -> split_disconnected_labels()
```

Browser:

```text
runSlicoLite()
```

The final int32 label maps must be exactly equal.

This is now a regression contract.

## Upstream isolation

After SLIC parity was closed, the full upstream path was tested from a canonical Python analysis RGBA input.

Browser executed:

```text
Python analysis RGBA
 -> Browser exact spectral L0
 -> Browser structural RGB
 -> Browser RGB-to-Lab
 -> Browser structural edge
 -> Browser SLIC
```

### Exact L0 result

The Browser exact spectral L0 output matched Python structural RGB exactly on all five cases:

- maximum absolute RGB error: **0**
- mean absolute RGB error: **0**

Therefore exact L0 is no longer the first-bad-stage.

### Lab result

Browser and Python Lab still differ.

Across the five cases:

- mean Lab absolute error: **0.0607**
- maximum Lab absolute error: **0.4159**

Per-case mean absolute error:

- Raden: 0.0683
- Subaru: 0.0986
- Noel: 0.0405
- Elizabeth: 0.0289
- Night River: 0.0671

### Structural edge result

Because edge is derived from Lab, a smaller residual also remains in structural edge:

- mean absolute edge error: **0.000244**

This small edge difference, together with the Lab difference, is sufficient to move SLIC boundary decisions.

## New first-bad-stage

The remaining upstream mismatch is now:

**RGB -> canonical Lab**

Python uses OpenCV float32 RGB-to-Lab conversion.

Browser uses an independent JavaScript CIELAB implementation.

Both are standards-based, but they are not numerically identical enough for pixel-exact SLIC decisions.

The next phase should target OpenCV-compatible Browser Lab conversion.

## End-to-end v6 benchmark

The five fixed cases were rerun through both Browser profiles.

### Lite

- mean processing: **849.0 ms**
- mean initial regions: **637.2**
- mean vertices: **1470.8**
- vs Python unguided proxy SSIM: **0.8503**
- vs Python unguided proxy edge IoU: **0.2574**
- vs Railway SSIM: **0.8371**
- vs Railway edge IoU: **0.2487**

### Exact

- mean processing: **10243.0 ms**
- mean initial regions: **645.2**
- mean vertices: **1553.2**
- vs Python unguided proxy SSIM: **0.8575**
- vs Python unguided proxy edge IoU: **0.2787**
- vs Railway SSIM: **0.8379**
- vs Railway edge IoU: **0.2589**

For reference, v5 exact was:

- SSIM: **0.8622**
- edge IoU: **0.2749**
- processing: **9646.5 ms**

v6 exact therefore improves edge overlap slightly but reduces aggregate SSIM slightly.

This is not treated as a SLIC regression.

The v6 SLIC implementation is exact on identical canonical inputs. The mixed end-to-end result is caused by the remaining Browser Lab mismatch feeding the now-exact SLIC implementation.

## Profile decision

No routing policy changes are made.

Normal Browser fallback:

```text
l0-lite-jacobi
```

Quality opt-in:

```text
?browserFallbackQuality=exact
```

Return to lite:

```text
?browserFallbackQuality=lite
```

Railway remains the final hosted escape hatch.

## Wrapper smoke

A real Chrome 64 x 48 generated PNG was passed through `minimalizeFile()` with both profiles.

Lite:

- mode: `browser-fallback-v6`
- compute: `browser`
- structural profile: `l0-lite-jacobi`
- palette: 8
- PASS

Exact:

- mode: `browser-fallback-v6`
- compute: `browser`
- structural profile: `spectral-exact`
- palette: 8
- PASS

Headers and metadata agree.

## Validation

Focused v6 / spectral / migration suite:

- **25 passed**

Full Browser / migration / Web / Local Worker regression:

- **74 passed**
- one existing Starlette/httpx deprecation warning

Also:

- JavaScript syntax: PASS
- `git diff --check`: PASS

## Gate result

### Canonical SLIC implementation: PASS, exact

Browser and Python produce identical SLIC label maps on identical structural inputs.

### Exact L0: PASS, exact on canonical analysis RGB

The spectral L0 output is pixel-identical in the five-case probe.

### Full Browser quality: MIXED

The exact profile gains edge overlap but does not improve aggregate SSIM over v5 exact.

### Railway graduation: HOLD

The remaining end-to-end gap is still material.

### Next first-bad-stage

**OpenCV-compatible RGB-to-Lab conversion parity**

## v7 target

Do not retune SLIC, Region Merge, or spectral L0 first.

v7 should focus on Lab conversion parity:

1. characterize OpenCV float RGB-to-Lab numerics across the full RGB cube or a dense deterministic sample;
2. identify differences in sRGB linearization constants, XYZ matrix constants, white point, epsilon/kappa branches, and float32 rounding;
3. implement an OpenCV-compatible Browser conversion path;
4. require low Lab error on deterministic fixtures;
5. rerun exact SLIC parity starting from identical structural RGB rather than precomputed Lab;
6. rerun the five-case Browser exact benchmark;
7. only after Lab parity closes, reassess the remaining contour-vertex gap.

The downstream contour gap remains visible:

- Python unguided mean vertices: **1000.8**
- Browser v6 exact mean vertices: **1553.2**

Contour simplification should remain secondary until the upstream Lab path is canonical.
