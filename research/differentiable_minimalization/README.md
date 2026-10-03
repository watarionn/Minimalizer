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
