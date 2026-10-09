# MinimalizerPublic R5: public-only read-only shadow browser canary

Date: 2026-10-10.
**R5 research integration complete / real Chrome ON-OFF-and-fallback output PASS / release HOLD.**

## Scope and chain

`watarionn/Minimalizer` branch `research/public-r5-readonly-shadow-browser-canary-20261010`, stacked on held R4 Draft #357, which depends on R3 #356, R2 #354 and R1 #353. Original v34 Draft #308 is separately held. **Do not merge this research stack to main or deploy** before Stage8, semantic source owner and visual approval gates.

No changes to `web/static/browser-fallback.js`, `local_worker/frontend/local-route.js`, MinimalizerLocal or production servers.

## What actually changed

- `web/static/public-r5-shadow-gate.mjs`: new local/browser ESM, no CDN/WASM requirement. Uses `Response.clone()` **after the normal Public conversion** to SHA-256-hash the already finished PNG. Enforces `image/png`, magic signature, 8MB memory cap, failed-hash and malformed-data status; retains only bytes+SHA/status in memory. The original Response object and PNG bytes are **never changed, consumed or replaced**.
- `web/static/public-route.js`: supports **strict OFF-by-default** `?publicR5Shadow=1`. Lazy import of the research-only module after normal engine completion; error returns an `unavailable` diagnostic without influencing output. No default HTML import or persistent storage.
- `scripts/verify_public_r5_route_chrome.py`: builds the real static Public bundle from the isolated research checkout and serves it on localhost. Uses genuine Selenium Chrome and actual `window.MinimalizerComputeRoute.minimalize(File)` for a full end-to-end conversion. Verifies OFF / ON and blocked shadow module / resvg-WASM.
- `tests/js/test_public_r5_shadow_gate.mjs` and `tests/test_public_r5_shadow_canary.py`: positive clone/hash assertions, injection of invalid MIME/PNG/oversize/hash failure, route/Local isolation and static build checks.

## Real browser result

Chrome **154.0.8037.98**. The input files were the three **frozen v32 already-minimalized PNG images** from `ConnectedSourcePlanesV32_20261009`, SHA-manifest verified. They are *deterministic conversion fixtures*, not the original character source photos. Therefore these tests **cannot** sign off output quality, source ownership, garment/arms/staff, or Golden subjective judgment.

| Input case | Public OFF generated PNG SHA-256 prefix | Public ON SHA-256 prefix | PNG bytes | Exact OFF vs ON |
|---|---|---|---:|---|
| Kyoko | 075264f97b33638a | same | 29,509 | **YES** |
| Noel | 332d48e15288caf0 | same | 25,585 | **YES** |
| Ririka | 317e75d5c0170fa8 | same | 23,494 | **YES** |

The separate shadow `sha256` value matches each complete original PNG. A **fresh, uncached Chrome** session with `public-r5-shadow-gate.mjs` and `resvg-wasm` blocked still converted and yielded the exact same Kyoko PNG SHA; status was `unavailable`. This is **fail-open for normal Public conversion**, not fail-open for release certification.

Tests through R5: **59 Python PASS** and six real Node browser-compatible observer safety scenarios PASS. Two independent real Chrome canary runs **PASS**; all eight outputs (3 OFF, 3 ON, one blocked module output and one JSON) were verified **8/8 byte-for-byte identical**.

## Gate distinction

- PASS: R5 runtime opt-in isolation, OFF/ON PNG byte equality for three frozen inputs and missing optional-observer/WASM fallback.
- HOLD: user Golden visual approval, genuine input photo -> output visual quality, source-grounded tie/arm/staff component ownership, Stage8 original contour vertex budget, resvg whole scene DPR2 renderer disagreement, iPhone Safari/device DPR, MPL-2.0 redistributable notices, and production monitoring/rollback review.
- The previously observed frozen R4 Chrome/resvg 680² mismatch comes from the pre-existing **frozen PNG Facet interpolation**; **paths-only Chrome/resvg remain bit-perfect at 340/680**. Do not treat path agreement as permission to rewrite Facet pixels.
- No new geometry or pixels added, no new facial features, no paint-order replacement.

## Next R6

Implement a deterministic release admission gate consuming the signed evidence reports and the outstanding human confirmations. The gate must hard-reject absent or false prerequisites; human Golden and independent iPhone Safari cannot be self-certified by a test. Create a NO-GO handoff until all gates genuinely pass; never merge while HOLD.
