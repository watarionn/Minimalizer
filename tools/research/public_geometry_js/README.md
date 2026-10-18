# MinimalizerPublic JS Geometry PoC | 2026-10-09

**Status: standalone, synthetic-first research ONLY. No import from web/static or local_worker.**

## Goal

Compare two external geometric tools without changing the canonical MinimalizerPublic browser path, Color Strip, original RGB policy, or ZeroBase/LocalWorker.

- Paper.js 0.12.18 (MIT): use real `new paper.Path`, `path.simplify(tolerance)`, `clone`, `flatten` and `pathData` to propose vector curves. Check protected original landmarks, exact source-resolution part mask (zero added pixels), allowable missing pixels and actual anchor reduction. Reject if any gate fails. DO NOT auto-publish even if candidate passes this preliminary raster audit.
- Delaunator 5.1.0 (ISC): `Delaunator.from(points)` triangulates grid points **within one independently verified semantic part**. Reject triangles with ANY rasterized source-pixel center outside that part. Fill each accepted triangle with source RGB from a pixel within that same verified part, never an invented color. A hole or neighbor part must remain uncovered.

**Important constraints:** Delaunator is *not* a constrained polygon triangulator, and Paper.js doesn't identify hair/face/arms. Neither fixes missing semantic masks. Pixel-center raster verification is a prototype gate, not a subpixel/SVG-renderer or cross-browser guarantee. In particular, output polygon edges can span subpixel slivers beyond the source mask, and Paper SVG antialiasing may differ from the flattened-curve raster audit. Both outputs are **candidateOnly** and cannot replace canonical contours without a later full topology, color, cross-browser and visual gate.

## Reproduce

Requires Node.js and npm. Run only in this directory, not the production web directory:

```sh
npm ci --ignore-scripts --no-audit --no-fund
npm test
npm run demo -- ./out
```

`out/synthetic-triangles.svg`, `out/synthetic-paper-path.svg`, and `out/metrics.json` are diagnostic examples; do not confuse these with real-image quality proof. The tests use original-source-shaped synthetic masks and strict provenance/extra-pixel checks. Packages and transitive dependency integrity hashes are pinned by package-lock.json; no CDN or production dependency is added.

## Release / next gate

1. Use original GC001/Kyoko and Raden verified masks, not guessed or fake synthetic source masks. Keep SHA/provenance references and pre-existing protected tie/arm/hair boundaries.
2. Produce source / canonical / Paper / Delaunator PNG+SVG comparisons; verify exact RGB samples, zero extra color footprint, thin arm gaps, silhouette, face boundary, counts and SVG rasterizer behavior.
3. Compare diagnostic two-character outputs visually, run existing browser regression and deterministic replay; only then consider an **optional** browser-geometry variant. No automatic production promotion, merge, or deployment in this PoC.
4. Avoid introducing native graphics, GPU, ML models or heavy dependencies into Public merely to run this research.
