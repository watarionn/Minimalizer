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

### Executed test evidence

- Real npm UMD loaded in Node VM and actual `SVGPathCommander` instance methods called.
- `node tests/js/test_public_svgpath_research.cjs`: **7 scenarios PASS**. A rectangle source ring produced bounding box (2,2)–(12,10), exact perimeter **36**, and remained immutable. Holes (2 rings), fractional coordinate loops, malformed source, bounded inputs, oversized dimensions and missing library handled without rendering changes.
- `python -m pytest tests/test_public_svgpath_research.py tests/test_public_earcut_research.py tests/test_public_delaunator_mesh.py tests/test_public_simplify_research.py tests/test_public_polygon_clip_integration.py tests/test_minimalizer_page_split.py -q`: **23 tests PASS**.
- `node --check` on new Public observer, Public route and browser fallback: PASS.
- Built Public static release (`dist/shin`) loaded in real desktop Chrome. The actual `MinimalizerComputeRoute.minimalize(file)` path converted the same controlled 64×64 PNG twice:
  - Default URL: status 200, `SVGPath-Audit: disabled`, 24 output shapes, existing `polygon-clipping` audit `ok`.
  - `?publicSvgPathResearch=1`: status 200, `SVGPath-Audit: truncated` (8-shape research cap), **8 parsed rings, 8 exact geometric bbox matches**, 24 output shapes, existing polygon clipping audit still `ok`; other optional Earcut audit remained disabled.
  - PNG **SHA-256 identical** with research OFF/ON: `c0ce3b408de0ab2c811306e99f15f923db2699cebb5f22b60cf7890e854f6c7d`, 552 bytes both. Subject guidance was disabled only in isolated smoke harness, not in shipped Public application code.
- Truncation of the 8-shape observer explicitly does not certify the remaining 16 shapes, and bbox comparison does not establish source-pixel/color/SVG/browser antialias parity.

## Future library roadmap

Next: SVGO isolated SVG serializer optimization under explicit no-pixel-change parity, or resvg-wasm independent SVG raster QA. These later steps should avoid changing the MinimalizerPublic product-completion pipeline automatically.
