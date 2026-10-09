# resvg-WASM library provenance and notices

- Package: `@resvg/resvg-wasm@2.6.2` (Mozilla Public License 2.0).
- Publisher source: https://github.com/yisibl/resvg-js (now https://github.com/thx/resvg-js).
- Distribution: official npm package `@resvg/resvg-wasm@2.6.2`, unmodified `index.mjs`, `index_bg.wasm` and `package.json` extracted via `npm pack`.
- Package archive SHA-256: `ff51acbb5ee0074601b75c3bea9226a18d346752af787f6d2d3adcdd98493d71`.
- WASM binary SHA-256: `22bf6e9f9a100d972da0411a69c5ba504367fc1fa87b3b64e3f35e53926d2d70`.
- Full MPL-2.0 license: `LICENSE` copied from upstream `thx/resvg-js/LICENSE` (Git blob `fa0086a952236971ab37901954d596efae9f4af6`). The npm tarball did not itself include a separate LICENSE file.
- Original source and build toolchain are available in the upstream repository; this trial does not modify the WASM covered code.
- WASM embeds Rust components, so transitive upstream attributions and source availability under MPL 2.0 require independent distribution compliance review before any website deployment.
- This vendored asset is only dynamically imported after an explicit MinimalizerPublic `?publicResvgResearch=1` request. No CDN, remote inference, user-image upload, or LocalWorker access.
- This is a research-only artifact, not permission to ship the public deployment without license compliance and release checks.
