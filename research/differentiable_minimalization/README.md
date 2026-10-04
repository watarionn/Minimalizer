# diffvg isolated runtime

P1 decision: use a disposable Linux container, never the Minimalizer production Python environment.

Build:
docker build -t minimalizer-diffvg-poc -f research/differentiable_minimalization/Dockerfile .

The diffvg revision is pinned. The adapter remains optional and research-only.

## 2026-10-03 environment probe

- Native Windows: PyTorch present, but pydiffvg/transformers absent and no usable C++ build toolchain was found.
- WSL Ubuntu exists but is not the canonical project environment.
- Docker Desktop Linux engine is available.
- A direct native pip attempt was stopped at recursive-submodule setup.
- The first Docker build was also stopped while the Debian package step produced no progress. Therefore P1 runtime reproducibility is **HOLD**, not falsely marked PASS.

P1 can close only after a clean container build plus a differentiable render/gradient smoke. P0 objective contracts remain valid and production is unchanged.


## P1 retry result — core runtime PASS / Python wrapper PARTIAL (2026-10-03)

The earlier apparent Docker stall was a false diagnosis: the Debian C++ toolchain download simply had long quiet intervals. The exact blockers were isolated:

1. upstream pyproject uses Poetry packaging that cannot locate a `diffvg` Python package at this pinned revision;
2. bundled pybind11 is too old for Python 3.11;
3. Python 3.10 builds the native CPU module successfully, but upstream setup.py expects a CPython-tagged filename while CMake emits plain `diffvg.so`.

The research Dockerfile now pins Python 3.10, CPU-only mode, the exact diffvg commit and submodules, bypasses the incompatible Poetry packaging, and copies the successfully built native module explicitly. Reproducible smoke result: `import diffvg` => `DIFFVG_CORE_OK`.

The higher-level `pydiffvg` wrapper still needs its optional Python dependencies (first observed missing dependency: scikit-image), so the runtime is **PARTIAL PASS**, not yet ready for real-image optimization. Production remains untouched.


## P1 completed — differentiable geometry smoke PASS (2026-10-03)

The CPU-only pinned diffvg/pydiffvg environment is now reproducible in Docker. Required wrapper dependencies were narrowed to the imports exercised by upstream pydiffvg and added to the research image.

A 64x64 ellipse smoke test proves the intended Minimalizer mechanism without any image generation: render an existing primitive, compare it with a fixed target raster, backpropagate MSE through diffvg, and update only the primitive center/radius. The first-step center and radius gradients were finite and non-zero. With Adam lr=0.25, gradient clipping and bounded geometry, loss fell from **0.12326050 to 0.00917053** in 40 steps (about **92.6% reduction**).

An intentionally more aggressive optimization attempt also exposed a useful guardrail: unconstrained geometry can drive diffvg into a native finite-shape assertion. Therefore P2 must use bounded parameterizations/clamps plus finite-gradient checks before accepting any candidate.

**Decision: P1 PASS.** Proceed to P2: adapt existing Minimalizer `VectorScene` rectangle/ellipse/polygon parameters into differentiable tensors, keep topology fixed for the first pass, and evaluate candidate geometry through the existing hard identity/minimality acceptance contract. Production routing remains unchanged.
