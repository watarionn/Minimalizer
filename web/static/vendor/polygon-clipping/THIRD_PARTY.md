# Public browser library: polygon-clipping

- Package: `polygon-clipping@0.15.7`
- Repository: https://github.com/mfogel/polygon-clipping
- License: MIT; full required attribution is preserved in `LICENSE.md`
- Exact npm package UMD-minified file SHA-256 **before** stripping the trailing sourcemap comment: `7f8619e84a86ce8dd400c9b50430e9c8cf8f26027b19eeb479f109f5c1a9d688`
- Vendored JavaScript file SHA-256: `d4ba992fe5d1b47f6531d18451719d724fb03d554f2630984cb504f72c599725`.
- Only the trailing `//# sourceMappingURL` comment was removed to avoid a reference to an unshipped source map. Minified executable code is otherwise from the pinned npm distribution.
- Loaded in `web/static/index.html` only. No network CDN or runtime npm install. The Public static builder copies this and the license verbatim.
- `public-polygon-geometry.js` invokes the clipping implementation as a **non-authoritative geometric diagnostic**, not to generate, recolor or replace source geometry. Fail-open on unavailable or rejected geometry.
- Do not load this library in MinimalizerLocal or import the Python-only `pyclipper` research.
