# L07 Lane B: executable Service Worker behavior preflight (2026-10-16)

Scope: research/test-only on `engineering/local-l07-vm-contract-20261016`. No runtime, Worker, Public/C08, deployment, private source or Golden modifications.

## Verification
- Node 22 `node --test tests/js/test_local_l07_sw_behavior.mjs`: **21/21 PASS** against the byte-for-byte `main` Service Worker script in a synthetic `node:vm` environment (offline/online shell fetches, eight install assets, bypass for API/uploads/private/generated images, POST and foreign origin).
- The real Service Worker file on `main` was directly read via GitHub. This is executable event-handler simulation, not Safari, actual browser, or a live LocalWorker network test.
- **New diagnostic blocker:** current `activate` deletes **all** same-origin cache names other than `minimalizer-local-shell-v1`, including unrelated cache namespaces. The test intentionally records current behavior, not approval. Future fix must restrict deletion to `minimalizer-local-shell-` prefix, with a failing-before/fixed-after regression and separately approved runtime patch.
- **Separate adapter diagnostic:** `local-route.js` marks a BEST HTTP 200 result as `qualityTier=best` without validating the `x-minimalizer-route` header, whereas `resultLabel` uses that header. This can produce inconsistent labels if a proxy or backend changes the response. Do not alter runtime until verified against real response contracts.
- Additional synthetic local-route fallback harness passed 9/9 locally but its repository upload was not completed; do not count it as a committed test.

## Gates
L07: **HOLD**. Live owner identity, Origin, 429, real Service Worker cache migration, Tailscale and iPhone Safari E2E remain untested here. L02 HOLD, Golden HOLD, production NO_GO. Do not infer security certification from isolated VM tests.

## Next steps
1. Add a safe, separate runtime proposal to restrict activation deletion to the app-owned cache prefix, with a regression that fails on the current script. Do not deploy without explicit promotion review.
2. Add route-header consistency and BEST/V2 fallback behavior tests to the repo (synthetic test only).
3. Verify real Worker response headers/owner/Origin/429 in a non-production environment and Safari install/offline/online by the user.
