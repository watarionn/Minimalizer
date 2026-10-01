# Browser Fallback v12 - Railway Graduation

Date: 2026-10-01

## Goal

Close the remaining Railway-graduation prerequisites from Browser Fallback v11.

v12 moves the public runtime to a static-hostable architecture:

1. Local Worker when the owner browser has opted in and the worker is ready.
2. Browser Fallback v12 when Local Worker is unavailable.
3. Browser Fallback v12 directly for browsers without Local Worker opt-in.

The public frontend no longer requires a hosted Minimalizer image-processing API.

Railway outputs remain useful only as the frozen parity reference used by this benchmark.

## What v12 closed

### Browser-side subject guidance

The browser runtime now ships analytical u2netp subject guidance with self-hosted ONNX Runtime WASM.

Required runtime assets are under:

```text
web/static/models/u2netp.onnx
web/static/vendor/onnxruntime/
```

No generative image model is used.

### Pillow-compatible Lanczos

Browser Subject preprocessing now includes a Pillow-compatible 8-bit Lanczos implementation.

This closed the largest remaining subject-mask mismatch, especially the Omaru Polka regression.

Final Polka comparison against the captured Railway reference:

- SSIM: 0.995299
- edge IoU: 0.972237
- MAE: 0.276399
- subject resize: `pillow-lanczos+lanczos-source`

### PNG hidden-RGB / alpha compositing parity

The browser subject decoder preserves unpremultiplied RGB where possible and composites alpha to white using the production-compatible path.

This matters for transparent PNGs whose hidden RGB affects resize/input parity.

### Large-source guard

The browser runtime does not blindly materialize native RGBA for arbitrarily large inputs.

Current limits locked by tests:

- native RGBA path limit: 12,000,000 pixels
- hard source limit: 100,000,000 pixels
- file limit: 64 MiB

Measured smoke:

- source: 5000 x 3000 = 15,000,000 pixels
- route: `canvas-large-source`
- status: 200
- analysis size: 100 x 60
- processing: about 268 ms for the reduced smoke profile
- dedicated headless-Chrome working-set peak: about 570.5 MiB

The memory number is an approximate process-group measurement, not a universal browser guarantee.

### Browser-native Color Strip and feature palette

Color Strip and the feature palette run from self-hosted browser code and no longer require the hosted service.

### Static Shin package

`scripts/build_shin_static.py` produces a static document root under:

```text
dist/shin
```

During v12 closure, a packaging bug was found: the original builder copied only top-level files and omitted nested model/runtime assets.

The builder now recursively includes the static tree, and the graduation tests explicitly require:

- `static/models/u2netp.onnx`
- `static/vendor/onnxruntime/ort.wasm.min.mjs`
- `static/vendor/onnxruntime/ort-wasm-simd-threaded.wasm`

Local static-host smoke returned HTTP 200 for the page, app code, Browser Subject module, model, ORT module, and WASM binary.

### Local Worker public-origin configuration

The final public HTTPS origin is intentionally not committed to the repository.

Configure it with:

```powershell
.\scripts\set_local_worker_origin.ps1 -Origin "https://<production-origin>"
```

The value is stored under `%LOCALAPPDATA%\Minimalizer\config\public-origin.txt` and loaded by `start_local_worker.ps1`.

## Final 16-case parity benchmark

The final v12 representative run completed 16/16 cases.

Against the captured Railway V2 reference outputs:

- mean SSIM: 0.990127
- minimum SSIM: 0.965018
- mean edge IoU: 0.841597
- minimum edge IoU: 0.378482
- mean MAE: 0.791492
- maximum MAE: 4.736071
- mean Browser Exact processing time: about 12.12 s
- mean browser u2netp inference time: about 1.20 s

Worst SSIM / MAE case:

- Elizabeth Rose Bloodflame
- SSIM 0.965018
- edge IoU 0.755556
- MAE 4.736071

Lowest edge-IoU case:

- Ichijou Ririka
- SSIM 0.973833
- edge IoU 0.378482
- MAE 1.123152

The low Ririka edge IoU is not paired with a large global image error; SSIM and MAE remain close to the reference.

The machine-readable summary is:

```text
docs/benchmarks/browser_fallback_v12_20261001.json
```

## Regression gate

Command:

```text
pytest tests/test_browser_fallback_v12.py tests/test_railway_graduation_v12.py -q
```

Measured after the Shin nested-asset packaging fix:

```text
32 passed
```

The suite locks:

- v12 Browser Subject contract
- Pillow-Lanczos availability/order
- no Railway or hosted Minimalizer API dependency in the static runtime
- self-hosted Browser Color Strip / feature palette
- deterministic large-source guard values
- complete Shin static package including nested ONNX/WASM assets
- Local Worker origin configuration outside the repository
- rejection of stale Browser Fallback v11 UI labels

## Gate status

### Semantic guidance gap: PASS

Browser u2netp guidance is implemented and verified on the representative corpus.

### Resize/decode residual: PASS

Pillow-compatible Lanczos plus the unpremultiplied/alpha-composite path closed the dominant regressions to the level captured by the final benchmark.

### Exact runtime: ACCEPTED

Exact remains materially heavier than Lite, with the final representative mean near 12.12 seconds.

This is a quality fallback, not a latency-equivalent replacement for Local Worker.

### Large-image memory: PASS

The 15 MP smoke entered the guarded large-source path and completed successfully.

### Static packaging: PASS

Nested model and ONNX Runtime assets are now part of the Shin package and are regression-tested.

### Railway runtime dependency: PASS

The static frontend contract contains no Railway endpoint and no hosted Minimalizer processing API route.

### Live Shin cutover: PENDING DESTINATION CONFIG

The repository and connected project documents do not contain the actual Shin Free Server production origin / document-root destination.

That is now the only deployment-specific input still required for the live cutover.

## Graduation decision

**Browser Fallback v12 is code-ready for Railway graduation.**

Do not describe the live migration as complete until the Shin production destination is configured, the public origin is written to the Local Worker allowlist, the static package is deployed, and the deployed origin passes the same static/runtime smoke checks.

No additional Railway compute work is required by the current runtime design.
