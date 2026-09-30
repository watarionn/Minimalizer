# Browser Fallback v4

Status: **STRUCTURAL PREPROCESSING IMPROVED / RAILWAY GRADUATION HOLD**

Date: 2026-09-30  
Branch: `feature/browser-fallback-v0-20260930`  
Production default: **unchanged**. Railway remains the hosted escape hatch.

## Goal

v4 improves the browser-owned structural preprocessing that feeds SLIC.

v3 already proved that the downstream Region Merge hierarchy and Minimal hierarchy cut are correct when they receive the same canonical inputs as Python.

The remaining upstream path was:

```text
analysis RGB
 -> structural RGB
 -> structural Lab
 -> structural edge
 -> SLIC
```

Python V2 uses FFT-based L0 gradient smoothing for `structural RGB`.

Browser v3 still used the unsmoothed analysis image for SLIC.

## Isolation result before implementation

The Browser SLIC implementation was tested with Python canonical:

- structural Lab
- structural edge

On the five fixed cases:

- mean SLIC boundary IoU: **0.9447**
- Browser -> Python region purity: **0.9916**
- Python -> Browser region purity: **0.9916**

This showed that SLICO-lite itself was already close to canonical behavior.

The dominant mismatch was structural preprocessing.

## Why not port the FFT implementation directly in v4

The canonical Python L0 smoother repeatedly solves a periodic 2D frequency-domain system using FFT.

A direct browser port would require:

- a new arbitrary-size FFT implementation or bundled runtime;
- repeated 2D transforms for arbitrary dimensions such as 281 and 311;
- substantially more code and runtime complexity.

v4 first evaluated spatial-domain approximations of the same L0 objective.

### Jacobi exploration

The candidate keeps the canonical outer L0 gradient-threshold rule, but approximates the linear solve with damped Jacobi iterations.

Python-side exploration showed:

- no structural smoothing: mean canonical SLIC boundary IoU **0.6726**
- beta 20 / 4 iterations: **0.7008**
- beta 100 / 8 iterations: **0.7080**
- beta 100 / 16 iterations: **0.7159**

### Conjugate Gradient exploration

CG improved approximation accuracy but was too expensive for a browser fallback.

The strongest tested profile reached:

- SLIC boundary IoU: **0.7382**
- Python-side runtime: about **4.1 s**

That was rejected for v4.

## L0-lite Jacobi implementation

Browser v4 adds `approximateL0StructuralRgba()`.

The implementation retains:

- canonical `lambda = 0.010`;
- `kappa = 2.0`;
- periodic horizontal and vertical gradients;
- vector RGB gradient thresholding;
- canonical divergence form;
- iterative solve of the same linear system;
- deterministic output.

The browser solve is a damped Jacobi approximation rather than the canonical FFT closed-form solve.

Selected profile:

```text
beta max: 100
Jacobi iterations per beta: 16
omega: 0.80
```

The output path is now:

```text
analysis RGBA
 -> L0-lite structural RGBA
 -> structural Lab
 -> canonical 3-channel Lab edge
 -> SLICO-lite
 -> canonical Region Merge v3
 -> Minimal hierarchy cut
 -> palette
 -> contour
```

## Profile sweep

Three browser profiles were measured on the fixed five-case benchmark.

| Profile | Processing | Initial regions | Vertices | Proxy SSIM | Proxy edge IoU |
| --- | ---: | ---: | ---: | ---: | ---: |
| fast: beta 20 / 4 iter | 528.4 ms | 645.2 | 1550.2 | 0.8328 | 0.2362 |
| beta 100 / 8 iter | 649.3 ms | 640.2 | 1482.6 | 0.8503 | 0.2567 |
| **beta 100 / 16 iter** | **851.0 ms** | **636.6** | **1472.4** | **0.8517** | **0.2592** |

The 16-iteration profile is the v4 default.

It gave the best measured:

- proxy SSIM;
- proxy edge IoU;
- contour vertex count;

while staying below one second of core processing on the tested PC.

## Final five-case result

Browser v4 final:

- mean processing: **851.0 ms**
- mean initial regions: **636.6**
- selected regions: **40**
- palette: **8**
- mean vertices: **1472.4**
- vs Python unguided proxy SSIM: **0.8517**
- vs Python unguided proxy edge IoU: **0.2592**
- vs Railway SSIM: **0.8337**
- vs Railway edge IoU: **0.2502**

Historical browser comparison:

| Version | Proxy SSIM | Proxy edge IoU |
| --- | ---: | ---: |
| v2 | 0.8364 | 0.2188 |
| v3 | 0.8335 | 0.2243 |
| **v4** | **0.8517** | **0.2592** |

v4 therefore improves both full-image similarity and edge overlap over the previous Browser fallbacks.

## Final preprocessing parity

With the selected 16-iteration profile:

- mean canonical structural RGB MAE: **2.474**
- mean canonical SLIC boundary IoU: **0.7099**
- Browser -> Python region purity: **0.9469**
- Python -> Browser region purity: **0.9471**

For comparison, when Browser SLIC receives the exact Python structural inputs:

- boundary IoU: **0.9447**
- purity: about **0.9916**

This isolates the remaining discrepancy to structural preprocessing rather than SLIC itself.

## v3 Region Merge contract remains fixed

v4 does not retune the downstream merge system.

The v3 parity contract remains:

- canonical merge-cost math;
- boundary histograms;
- safe consolidation;
- complete merge hierarchy;
- Minimal visual-loss DP cut;
- exact final partition on identical canonical inputs.

The automated parity test remains part of the v4 suite.

## Browser metadata

The browser response now exposes:

- `X-Minimalizer-Mode: browser-fallback-v4`
- `X-Minimalizer-Compute: browser`
- `X-Minimalizer-Structural-Preprocess: l0-lite-jacobi`
- `X-Minimalizer-L0-Jacobi-Iterations: 16`

The normal shape / palette / hierarchy metadata is retained.

## Validation

Focused regression:

- **69 passed**
- JavaScript syntax: PASS
- `git diff --check`: PASS

Real Chrome wrapper smoke:

```text
File
 -> browser-fallback-v4
 -> l0-lite-jacobi
 -> SLICO-lite
 -> canonical Region Merge
 -> 40-region cut
 -> palette 8
 -> PNG Response
```

PASS.

## Gate result

### Structural preprocessing: PASS, improved

L0-lite materially improves the browser fallback and is accepted as the v4 preprocessing path.

### Region Merge: PASS

Inherited unchanged from v3 parity work.

### Full Browser quality: IMPROVED

Both proxy SSIM and edge IoU are the best Browser fallback results so far.

### Railway graduation: HOLD

The browser route is still not close enough to the Python unguided proxy to remove Railway yet.

The Python unguided proxy versus Railway baseline remains:

- SSIM: **0.9067**
- edge IoU: **0.5332**

## New first-bad-stage

The remaining upstream gap is narrower now:

**canonical FFT L0 structural smoothing fidelity**

The evidence is:

1. Region Merge is exact on identical inputs.
2. Browser SLIC is already highly aligned on identical structural inputs.
3. L0-lite improves full Browser quality.
4. The final SLIC partition still differs substantially before Region Merge.

## Browser Fallback v5 target

Do not retune Region Merge first.

v5 should investigate a higher-fidelity browser structural smoother:

1. evaluate an arbitrary-size spectral solver suitable for static browser delivery;
2. compare pure JS, WebAssembly, and possibly GPU-assisted implementations;
3. keep all assets self-hosted and offline-capable;
4. directly measure structural RGB parity before full-pipeline testing;
5. require a meaningful SLIC boundary-IoU gain over v4 before adoption;
6. retain L0-lite as the safe fallback if the exact spectral route is too slow or complex.

Railway remains in place until the Browser route closes more of that structural gap.
