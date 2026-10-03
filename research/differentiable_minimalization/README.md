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
