# L07 non-destructive Local PWA cache/privacy preflight (2026-10-16)

**Static source privacy boundary: generation-pinned and namespace-scoped cache migration. Live LocalWorker/iPhone/E2E: NOT TESTED. L07 formal: HOLD. L08 and L02 remain HOLD, production NO_GO.**

This work runs in parallel with the L02 garment/arm semantic hold. It stages a bounded Local Worker cache-policy change only; it does not touch production deployment, Public/C08, Golden or iPhone acceptance. The authoritative GitHub main Local assets were directly read back by the connected GitHub API:
- `local_worker/frontend/sw.js` Git blob `9dcf1b658e7c4160a4ce7d9efd0e91242559cbe2`.
- `local_worker/frontend/local-route.js` Git blob `88ff8eac22ba6f6bb54851fa7499fced1522df0c`.

The SW explicitly caches the fixed eight-file private app shell, including the entry page, JS/CSS and icon. It does NOT cache uploaded images, generated outputs, arbitrary GET responses or `/api/...` requests. Fetch events are intercepted only for **GET, same-origin, exactly-whitelisted pathnames** and otherwise bypass the worker fetch handler. The matching path uses network-first with cached shell fallback. The SW cache name and registration query are pinned to the same generation `minimalizer-local-20261107-1`, registration uses `updateViaCache: "none"`, and activation deletes only older caches in the `minimalizer-local-shell-` namespace; foreign caches are not deleted by this contract. The private adapter waits for the LocalWorker `/health` ready flag before requesting the BEST endpoint; it explicitly uses Local V2 fallback and has no BrowserFallback route. The exact source passed the fail-closed static inspection, not a simulated live Safari/browser test.

The generation transition is now deliberately lifecycle-safe: the worker does
not call `skipWaiting()` or `clients.claim()`. An already-open page therefore
remains under its existing worker generation, while the newly installed shell
waits for the browser's normal next-navigation activation. The static audit
rejects either immediate-claim API so a future edit cannot silently reintroduce
cross-generation control of an open page.

Offline fallback also canonicalizes an allowed shell request to its pathname
before `caches.match`. A query-bearing shell request therefore falls back to
the installed generation entry instead of missing because the cache key has no
query string; API, upload, and arbitrary image requests remain outside the
fetch handler.

Two source-free research files are added:
- `tools/research/local_l07_pwa_privacy_audit.py` for fail-closed static privacy contract checks; intended usage `python tools/research/local_l07_pwa_privacy_audit.py .`.
- `tests/test_local_l07_pwa_privacy_audit.py` with explicit negative cases for API and image cache poisoning, removed origin/GET/allowlist checks, dynamic cache.put, second fetch handler, browser downgrade, absent health/BEST paths and false live-test claims.

**Test evidence boundary:** the focused suite includes the generation pin and foreign-cache cleanup negative case. The static audit returns `STATIC_SW_PRIVACY_CONTRACT_PASS`, generation `minimalizer-local-20261107-1`, and `STATIC_LOCAL_ROUTE_ISOLATED`. This is not a live e2e or proof that all browser update, Origin, Tailscale, Safari or device flows succeed.

At the time of this static audit, remaining L07 work included a running LocalWorker `Origin`, Tailscale owner identity, preflight, device-browser lifecycle and physical iPhone acceptance. Do NOT sign off solely from these read-only checks. The later production and iPhone evidence below closes the L07 device gate; L02 research continues independently.

Security/quality non-promotion: user-supplied source pixels, private NPZ, canonical Phase4 owners and manual Golden unchanged; no generated visible pixels; no eyes/nose/mouth/brows drawn; Public/C08 and Local production untouched.

## 2026-11-09 production browser registration

After PR #454 merged as main commit
`c68dc17bdc2bd3b0ba0841b7108177553891913c`, the production LocalWorker was
restarted from that exact checkout. Private HTTPS readback returned HTTP 200
for `/`, `/sw.js`, and `/local-static/local-route.js`; the latter two were
missing from the prior production checkout.

An isolated, fresh-profile Chrome loaded the private-tailnet HTTPS entry page.
Chrome's own DevTools target inventory then reported one active Service Worker
with the exact registered script URL:

`https://ywshtmr.tail8fd68c.ts.net:28765/sw.js?generation=minimalizer-local-20261107-1`.

This proves a real browser registered the production generation-pinned worker,
in addition to the static audit. It does not substitute for physical iPhone
install/offline/update acceptance, which remains the final L07/L05 device gate.

## 2026-11-09 physical iPhone acceptance

The owner accepted the private Local PWA on iPhone: Safari and the installed
PWA each completed a PNG operation, and an airplane-mode round trip followed
by restored connectivity continued to work. The private evidence receipt has
SHA-256 `06f09cfba8958a7214a86157ea19ad64c49c3ba876e65ca2c908c9cf70b91fea`;
raw screenshots remain outside GitHub. The observed fallback from a ZeroBase2
503 to a successful Local V2 result is consistent with the no-browser-fallback
contract. This closes the L07 iPhone device gate without changing Public/C08,
Golden, signed originals, or L02/L04 artifacts.
