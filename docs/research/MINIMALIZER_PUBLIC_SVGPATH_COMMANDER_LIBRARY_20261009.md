# MinimalizerPublic SVGPathCommander library introduction (2026-10-09)

## Scope

This chat installs and verifies useful **browser JavaScript/WASM dependencies** in MinimalizerPublic, not MinimalizerLocal's Python code and not the main product's final source fidelity / Golden / Safari / website deployment.

Previously merged Public libraries:
- polygon-clipping 0.15.7, PR #344: real viewport intersection audit.
- simplify-js 1.2.4, PR #345: optional source-mask-verified vertex-removal research.
- delaunator 5.1.0, PR #346: opt-in Delaunay triangulation of source-owner vertices.
- earcut 3.2.4, PR #347: opt-in polygon-with-holes triangles and whole-owner raster reconstruction.

## New module

- **`svg-path-commander@2.3.3` (MIT)** official npm browser UMD vendored in `web/static/vendor/svg-path-commander/index.min.js`, license and third-party provenance preserved. No CDN/remote servers.
- Public-specific adapter `web/static/public-svgpath-research.js` derives temporary SVG `M…L…Z` paths from current source owner rings. It uses the genuine package to parse paths, measure SVG path lengths, obtain path bounding boxes, and compare those numeric bbox corners against the unchanged ring points.
- Public `index.html` loads the vendor script and adapter before `browser-fallback.js`; Public URL `?publicSvgPathResearch=1` opts in. Default Public conversions keep `publicSvgPathResearch: false`.
- Existing browser converter invokes this **read-only diagnostic** only when opted in, and exposes `X-Minimalizer-Public-SVGPath-Audit`, `X-Minimalizer-Public-SVGPath-Rings`, and `X-Minimalizer-Public-SVGPath-BBox-Matches` response headers, plus full optional metrics in metadata.
- CPU/memory bounds: 8 shapes, 64 rings, 1800 path vertices, 60k characters, 160k canvas pixels. Invalid data skipped; missing library/errors reported, never mutate render output or owner points.
- No SVG file generation, no change to original contour, palette, face-feature policy or Python/Local route.

## Independent validation

Real npm UMD loaded in sandbox with callable static parser, path bbox and length. Synthetic rectangle expected bbox (2,2)-(12,10) and perimeter 36.

Browser validation and test counts are recorded after actual execution. Do not infer image-quality improvement, full scene source pixel equality, Golden or production readiness from this diagnostic.

## Future library roadmap

Next: SVGO isolated SVG serializer optimization under explicit no-pixel-change parity, or resvg-wasm independent SVG raster QA. These later steps should avoid changing the MinimalizerPublic product-completion pipeline automatically.
