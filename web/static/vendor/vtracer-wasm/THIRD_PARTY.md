# VTracer browser WASM provenance

- Browser-capable npm distribution: `vtracer-wasm@0.1.0`, https://www.npmjs.com/package/vtracer-wasm; publisher source https://github.com/jsscheller/vtracer-wasm. This is a third-party browser package, **not the official @visioncortex/vtracer Node.js package**.
- npm archive SHA-256: `da0fe09e41ad0b9371453b22cdef73363381cbcb4f4c97ce2659f8db5a2a6f66`.
- Actual WASM SHA-256: `b93108af0f23e13a64f4b23f2582312a325be9d7ff833e49d04554cd99606f0b`.
- Unmodified `vtracer.js` from package copied as `vtracer.mjs` (extension-only change), matching unmodified `vtracer.wasm` and `package.json`.
- Wrapper license MIT, original npm archive `LICENSE` preserved. Underlying VTracer origin is https://github.com/visioncortex/vtracer (MIT OR Apache-2.0); upstream `LICENSE` also copied here as `LICENSE-VTRACER-UPSTREAM`, source blob `f8fd70d24eba800637de70c368b989e2a763550a`.
- The independent Rust dependencies, embedded notices, upstream code version, and any source/provenance requirements are **not yet completely audited**. A legal/release review is required before the published website can distribute this WASM.
- The official `@visioncortex/vtracer@1.0.0-alpha.4` npm tarball was inspected but its WASM/JS package is built for `wasm-pack --target nodejs` and requires Node fs, so it was not shipped or adapted into browser code.
- `?publicVTracerResearch=1` alone dynamically imports this module and fetches the same-origin WASM in MinimalizerPublic; normal mode does not fetch. No CDN, third-party inference, original uploaded image transmission, or LocalWorker.
- The observer traces only a bounded sample of the **already-rendered** Public result canvas; candidate SVG is never returned to or applied by the converter. Output image colors, silhouette, source ownership and facial-feature non-display policy remain unchanged.
