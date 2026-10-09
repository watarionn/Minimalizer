# MinimalizerPublic R8: vendor redistribution and disposable rollback checks

2026-10-10 | **R8 engineering PASS / LICENSE + PRODUCTION RELEASE NO-GO**.

## Scope and authoritative lineage

- R8 research branch `research/public-r8-license-distribution-inventory-20261010`, stacked on R7 Draft PR #360, R6 #359, R5 #358, R4 #357, R3 #356, R2 #354, R1 #353. Original v34 Draft #308 remains HOLD on a separate branch.
- No edits or deployments of production Static/Public route, Local Minimalizer, Local Worker, any original image, or signed Golden.
- R6 immutable canonical evidence gate still reports **7/15 PASS and 8/15 BLOCKED; release NO-GO**. R7 human source review is still UNSIGNED.
- Focus on two non-release machine-actionable barriers: verify research-only JavaScript/WASM license + attribution files really survive the existing static distribution build, and rehearse a byte-exact reversible static artifact switch in an isolated localhost server. Neither constitutes legal signoff or production rollback certification.

## Actual script changes

`scripts/verify_public_r8_license_distribution.py`:

1. Exhaustively enumerate the 9 already-vendored Public research libs: polygon-clipping, Simplify.js, Delaunator, Earcut, SVGPathCommander, SVGO, resvg-WASM, Clipper2-WASM, VTracer-WASM. Fail on unexpected or missing vendor directories/files (including legacy ONNX runtime and model license directory).
2. Record path, SHA-256, byte count and declared license of **all 40 source vendor files**. Confirm 9/9 include their `THIRD_PARTY.md` and full applicable `LICENSE`/license text. Verify pinned resvg 2.6.2 MPL-2.0 package name/version/license + exact official full MPL text; pinned resvg WASM SHA-256 `22bf6e9f9a100d972da0411a69c5ba504367fc1fa87b3b64e3f35e53926d2d70`. Verify VTracer WASM SHA-256 `b93108af0f23e13a64f4b23f2582312a325be9d7ff833e49d04554cd99606f0b`.
3. Execute the **real** existing `scripts/build_shin_static.py` builder with its output location redirected into a disposable temporary folder, never into the live output. Re-enumerate and SHA-compare **40/40 shipped vendor files**, including license text and third-party notices, byte-for-byte to original. Actual public entry `index.html` must also be byte-exact.
4. In a *second* disposable temp folder, serve the unchanged built `index.html` over actual loopback HTTP at `127.0.0.1`; temporarily serve a canary copy with a **test-only HTML comment** appended; then restore the exact saved production-style source via `os.replace`. Compare client-served content and SHA-256 after rollback. **This is a file-level/local HTTP simulation, NOT a real production deployment, user-facing canary, cache invalidation test, iPhone test or signed rollback.**
5. Produce only an audit JSON and a `RESVG_MPL_REVIEW_PENDING.md` checklist into a fresh output directory. Audit verdict `INVENTORY_PASS_LEGAL_HOLD`, `releaseAuthorized=false`, `existingR6BlockedGatesCleared=0` irrespective of success.

## Measurements from real Windows checkout

- Actual existing static build completed without source changes; nine research libraries and **40 vendor assets including notices LICENSE copied byte-exact 40/40**. Onnxruntime/u2net license notices also found in the static copied tree.
- Strict negative controls: missing resvg MPL LICENSE, tampered resvg binary, changed resvg license metadata, deleted `THIRD_PARTY.md`, unreviewed library directory, malformed rollback HTML and already-existing output folder are rejected.
- Loopback HTTP staged switch: original -> test-only canary -> restored original **100% byte-exact**; baseline and restored SHA-256 `31b6a03e722074aa5b9833e4f02cb250b29a81d64b0d7bca79ed5920d000e6b5`; synthetic canary differs as expected.
- **80 targeted Python regressions PASS** across R1–R8 + Local/Public isolation. Python compile PASS. Two independent full audit+build+localhost runs: **2/2 output files byte-exact** (inventory JSON, MPL pending handoff). JSON SHA256 `996d91002a1c3a39f021...` as abbreviated console report; preserve exact full hash via retained JSON.
- The output was generated **only** by existing tools/libraries, without CDN, generated imagery, image conversion, or GPU.
- Canonical results are intended for `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R8_20261010/`; final preservation must be read back before claiming it complete.

## Important non-pass determinations

**MPL-2.0 redistribution review is still UNSIGNED.** Matching LICENSE and THIRD_PARTY in a distribution folder alone does not establish compliance. Review actual shipped source code availability and precise recipients' notices, embedded Rust transitive licenses and the status of any modification; legal interpretation belongs to the qualified release reviewer. Mozilla's MPL-2.0 FAQ notes that client-side web files count as distributed and compiled MPL works may require notices describing where corresponding covered source is available. See:

- Official Mozilla FAQ: https://www.mozilla.org/en-US/MPL/2.0/FAQ/
- MPL-2.0 license: https://www.mozilla.org/en-US/MPL/2.0/
- Exact vendored resvg library `@resvg/resvg-wasm@2.6.2` provenance: https://www.npmjs.com/package/%40resvg/resvg-wasm

**Actual production rollback is also UNSIGNED.** Loopback demonstrates deterministic restore of the byte-identical entry point only. It does not test CDN/proxy caching, browser service worker, real live routing, incident recovery timing or product users.

**All 8 R6 release blockers remain BLOCKED:** R4 whole-scene DPR2 resvg/Chrome raster-Facet difference; user Golden; source/part semantics; tie/arms/staff/faceless protection; Stage8 original ring budget; genuine iPhone Safari DPR; MPL legal review; real production rollback. R7 has review packets, not actual sign-offs. Do not merge or deploy based on this machine audit.

## Next candidate R9 (fail-closed non-production)

Prepare a precise production rollback runbook with deploy-specific routing and cache invariants, preserve stage-8/semantic checkpoints, and add Safari-device review scripts without inventing a device run. Any release still requires independent human, device, license and original Stage8 evidence. R8 only closes the **machine evidence preparation stage**.
