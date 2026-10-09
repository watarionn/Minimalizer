# SVGPathCommander browser dependency

- Package: `svg-path-commander@2.3.3` (MIT), upstream https://github.com/thednp/svg-path-commander.
- Vendored from official npm `dist/index.min.js` self-contained browser UMD build. Original npm bundle SHA-256: `45a99d1438bd25a0e67e2623ed20c0ee418241d0d372a190b1f91522d1937a8c`; source text preserved except possible line endings/terminal newline.
- `LICENSE` is copied from the pinned package with full attribution.
- Public-only: load from `web/static/index.html`, never in MinimalizerLocal, no CDN, Python execution, or runtime package installation.
- Activation: `?publicSvgPathResearch=1`; otherwise the library is loaded but the diagnostic **does not execute**.
- Diagnostic reads existing owner ring vertices and calls actual `SVGPathCommander.parsePathString`, `getBBox`, `getTotalLength` and `toString` on a reconstructed temporary path. The source owner polygons, rendering and source RGB are not replaced.
- Geometry/bbox parity here is geometric evidence only; it does **not** certify source-accurate OpenCV raster, SVG DPR1/DPR4, browser anti-alias, Golden, Safari, or product release. All production-quality work is owned by the separate MinimalizerPublic completion conversation.
