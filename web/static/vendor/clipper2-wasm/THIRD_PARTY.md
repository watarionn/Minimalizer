# Clipper2-WASM provenance and third-party notices

- Upstream: ErikSom/Clipper2-WASM, https://github.com/ErikSom/Clipper2-WASM
- C++ upstream: AngusJohnson/Clipper2, https://github.com/AngusJohnson/Clipper2
- Package: official npm `clipper2-wasm@0.4.0` (license declared `BSL-1.0`).
- Self-hosted unmodified binary from npm tarball: `dist/es/clipper2z.wasm` relocated as `clipper2z.wasm`; SHA-256 `429e866b4d7813cabfa7d31e6650825343109fb7d7a1702c533e8597573449ec`.
- Self-hosted ES module from npm tarball: `dist/es/clipper2z.js` copied byte-for-byte under `clipper2z.mjs`; extension only is changed so the browser serves ESM MIME correctly.
- `LICENSE` copied from upstream repository root (Boost Software License 1.0). Original npm tarball does not contain a license file.
- `package.json` retained unchanged from official npm tarball, recording source, version and declared license.
- Only requested with `?publicClipper2Research=1` in MinimalizerPublic, not in LocalWorker; the .wasm URL is same-origin.
- Separate public-distribution compliance review should validate upstream and transitive attribution/provenance before deployment. Merely storing this LICENSE does not pass a website release gate.
- This library's output is research-only and NEVER applied to owner geometry, output SVG, output PNG, palette or facial feature policy.
