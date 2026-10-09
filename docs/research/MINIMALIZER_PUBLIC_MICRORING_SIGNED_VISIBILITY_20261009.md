# MinimalizerPublic micro-ring signed source visibility, 2026-10-09

**Research evidence PASS, deletion/reduction Gate HOLD.** Based on unchanged signed Stage8 two-character originals and independently verified source-visible owner-mask binary files. No raw private image or mask contents committed to GitHub.

| Source case | 1-2 point Stage8 rings | Ring vertices | Original source transparent samples | Outside own signed source-visible owner mask | Covered by later visible source owner |
|---|---:|---:|---:|---:|---:|
| GC001 | 110 | 163 | 0 | **0** | **0** |
| Raden | 13 | 17 | 0 | **0** | **0** |

SHA-256 checks were performed on source images and signed source-visible owner masks, using the private `verified_owner_manifest.json` from the SA10.34+SA10.41 research set. `__unbound__` was mapped only to the existing `unknown` signed owner. Preserved source back-to-front layer ordering.

For GC001, 96 micro-ring vertices are in the original `__unbound__` owner; a zero-count `outside mask` is not evidence that the semantic classification is correct. **Every sampled coordinate is source-paint-visible**, so the no-information assumption for tiny rings is contradicted. Mask point membership alone does not prove the ring is a unique visible primitive or that the complete original raster is modified by its deletion. The precise per-point coordinates and full masks are kept private.

Next release gate: independently rerasterize original vs individually deleted micro-rings, compare exact signed owner-mask pixels and topology, then verify DPR4 browser raster, z-order and non-face RGB. Until then, **approved safe deletions = 0**. Historical Stage8 source-ring budgets GC001 3,604>1,887 and Raden 2,370>1,412 stay failed. Face features hidden; production unchanged; human Golden HOLD.

Reproducibility: `tools/research/public_geometry_js/stage8_micro_visibility_gate.py` accepts staged private SHA-signed Stage8 JSON, signed visible mask directory and provenance manifest. Returned audit is aggregate only; never returns original source pixels.
