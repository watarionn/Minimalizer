# MinimalizerPublic R10 release-scoped assets, 2026-10-10

**Engineering PASS; production NO-GO; research-only Draft.** Based on R9 Draft #364 (R8 #361, R7 #360, R6 #359 and earlier stacked). Original v34 #308 remains separate and HOLD. No changes to original assets, Local Minimalizer, Local Worker, live Public route or deployed hosting.

## Problem and implementation

R9 reproduced stale `app.js` and `styles.css` on a simulated cacheable public host. R10 implements `scripts/verify_public_r10_release_assets.py` to create a disposable pair of full Public release asset trees:

```text
index.html
assets/<source-derived-release-id>/static/<66 assets>
```

The release ID is a deterministic 24-character prefix of SHA-256 over the ordered **original source file SHA mapping**, not an untrue staged-output hash. Every staged copied file retains its own independently recorded SHA. The actual existing static builder runs inside a temporary directory. R10 rewrites 24 HTML JS/CSS URLs and exactly five document-relative dynamic research-module imports on a copied `public-route.js`; the original source code remains unchanged. Other module-relative WASM and ONNX model references retain their path within the release directory. Unsupported/missing imports, unexpected source assets and existing output folders fail closed.

Two releases coexist in disposable folders; the synthetic new source app.js and styles.css have test-only comments, not changed processing logic. Pointer `index.html` switches from old to new to old again. Old URLs remain available to cached tabs throughout. Asset tests compare full-file SHA for six representative paths per phase (app.js, styles.css, public-route.js, browser-subject.js, resvg-WASM and u2netp ONNX). Cache simulation is deliberately hypothetical (HTML no-store, static assets max-age=3600); real Shin response headers were NOT measured.

## Actual measurements

- Real Chrome 154.0.8037.98: **four phases PASS** (initial, synthetic upgrade, old asset retention, rollback); **six representative file digests exact** per phase.
- Static source: **66 assets per release**, **24 HTML references rewritten**, **five dynamic imports rewritten**. Original release ID `a0ce6b5f2c0f8a9f5e2b03fe`; synthetic updated ID `7a8135fdaa88c14a9059399e`.
- Real Public browser conversion, using archived SHA-verified **already-minimalized** Kyoko v32 PNG as test fixture, gave identical output at baseline, canary and rollback: 29,509-byte output PNG, SHA-256 `075264f97b33638aab51cfc7351d3c4fec0ed3aa7e0b4a5b528a758d5fb7d971`. R5 read-only observer module was imported through the release-specific route and produced matching SHA each time. This is a **functional parity** test, NOT an original-photo or Golden visual-quality approval.
- Full R1–R10 and Local/Public isolation regression: **91 pytest PASS**. Negative tests include missing dynamic observer, stale/invalid asset URL, non-unique release ID and no-overwrite.
- Two independent full Chrome experiment replays yielded identical 23,359-byte JSON SHA-256: `fd3dc69e56dc7134558bcf18a4952855eddde9eb388484e35aec3a2db59ba735`.

## Boundary / remaining risks

R6 still has **eight release blockers**: full-scene resvg DPR2 mismatch, unsigned human Golden review, semantic source ownership and arm/tie/staff/face protection, original Stage8 vertex budget, real iPhone Safari, legal MPL redistribution and real production rollback. R10 is an immutable, reproducible **research generator**, not a deployed product change or host-certified rollback. Source-derived release IDs only mitigate browser caching when old release directories persist and the real host honors the required paths. No iPhone physical device or hosting CDN/cache checks were done.

Recorded status `RELEASE_VERSIONING_RESEARCH_PASS_PRODUCTION_NO_GO`, `releaseAuthorized=false`, `mergeOrDeployPerformed=false`. Next R11 may inspect real hosting capabilities and prepare a held deploy integration gate, but must not promote release without genuine signoffs.
