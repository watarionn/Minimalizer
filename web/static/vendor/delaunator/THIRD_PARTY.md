# Delaunator: MinimalizerPublic browser triangulation library

- Library: `delaunator@5.1.0` (Mapbox, ISC).
- Upstream: https://github.com/mapbox/delaunator
- Package file: `delaunator.min.js` from the exact npm 5.1.0 package, self-hosted as a standalone browser UMD bundle. The upstream npm-file SHA-256 is `bfe30439db2a04cb19e23525f7e203636e4faa4f1143876e649caba24629bab6`. Local Windows checkouts can normalize newlines; compare normalized source for a textual audit.
- Delaunator's ISC license appears in `LICENSE`.
- Bundled dependency: `robust-predicates@3.0.2` (Unlicense). The upstream `ROBUST_PREDICATES_LICENSE` is preserved alongside this bundled file.
- Public only: `web/static/index.html`; no CDN, npm runtime install or Python local worker.
- The independent Public `public-mesh-research.js` observer runs **only** with `?publicMeshResearch=1`. The default Public conversion does not run triangulation.
- No new pixels, source masks, SVG parts, materials, eyes, mouth, or ownership are generated. Candidate triangles are **never committed to output**; they are counted as owner-contained only when every pixel of each candidate triangle raster is within the original owner binary mask.
