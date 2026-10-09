# Earcut: MinimalizerPublic browser research library

- Package: `earcut@3.2.4`
- Upstream: https://github.com/mapbox/earcut
- License: ISC; the npm package `LICENSE` is preserved verbatim next to the browser bundle.
- Vendored source: `dist/earcut.min.js` from the published npm package, SHA-256 `29df76691215df89bf904051f35eb7aae1831011093d9783e843c3421931a334` (publisher file before repository text normalization).
- Public runtime only, self-hosted in `web/static/index.html`; no CDN, external model, Local Python/worker or runtime npm install.
- Research mode: `?publicEarcutResearch=1`. Normal MinimalizerPublic conversion does not execute triangulation.
- Earcut polygon rings are interpreted conservatively as outer ring with subsequent holes for a candidate. An independent, pixel-exact whole-owner raster gate is mandatory; a disjoint second outer ring is **not** approved by that interpretation.
- Each triangulated candidate is counted only when its raster is a subset of the source owner. A `fullyReconstructedShapes` count is issued only if the accepted triangle union equals the entire original owner mask pixel-for-pixel, the trial is complete, and no unsafe triangles remain.
- All output geometry and source pixels are left untouched; this is read-only research. Original/source-authoritative Stage8, faces, 40-shape Golden and iPhone Safari are outside this library-installation scope.
