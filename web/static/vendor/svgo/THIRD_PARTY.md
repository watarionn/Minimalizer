# SVGO browser dependency provenance

- Source: official npm package `svgo@4.1.0`, https://www.npmjs.com/package/svgo
- Upstream: https://github.com/svg/svgo
- Artifact: `package/dist/svgo.browser.js` from official `svgo-4.1.0.tgz`, unmodified.
- License: MIT, original `package/LICENSE` copied alongside this bundle.
- Source acquisition: `npm pack svgo@4.1.0` (no CDN, no remotely executed project script).
- Load boundary: only opt-in `?publicSvgoResearch=1` on MinimalizerPublic, dynamic import of `public-svgo-research.mjs`.
- Runtime PNG and SVG are never replaced by this browser bundle.

The official prebundled browser distribution contains third-party components.
SVGO 4.1.0's direct dependencies include:
`css-select` (BSD-2-Clause), `css-tree` (MIT),
`css-what` (BSD-2-Clause), `csso` (MIT),
`sax` (BlueOak-1.0.0), `picocolors` (ISC), and
`commander` (MIT; CLI, not necessarily in browser bundle).
Specific bundled/transitive attribution completeness is a separate release
compliance check, not satisfied merely by preserving the SVGO MIT license.
Do not deploy this experimental asset until that check is passed.
