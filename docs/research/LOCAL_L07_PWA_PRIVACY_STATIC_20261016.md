# L07 non-destructive Local PWA cache/privacy preflight (2026-10-16)

**Static source privacy boundary: 14/14 independent direct-GitHub checks PASS. Live LocalWorker/iPhone/E2E: NOT TESTED. L07 formal: HOLD. L08 and L02 remain HOLD, production NO_GO.**

This work runs in parallel with the L02 garment/arm semantic hold. It **adds no runtime/frontend/Worker modification**. The authoritative GitHub main Local assets were directly read back by the connected GitHub API:
- `local_worker/frontend/sw.js` Git blob `9dcf1b658e7c4160a4ce7d9efd0e91242559cbe2`.
- `local_worker/frontend/local-route.js` Git blob `88ff8eac22ba6f6bb54851fa7499fced1522df0c`.

The SW explicitly caches the fixed eight-file private app shell, including the entry page, JS/CSS and icon. It does NOT cache uploaded images, generated outputs, arbitrary GET responses or `/api/...` requests. Fetch events are intercepted only for **GET, same-origin, exactly-whitelisted pathnames** and otherwise bypass the worker fetch handler. The matching path uses network-first with cached shell fallback. The private adapter waits for the LocalWorker `/health` ready flag before requesting the BEST endpoint; it explicitly uses Local V2 fallback and has no BrowserFallback route. The exact source passed an independent 14-condition static inspection, not a simulated live Safari/browser test.

Two source-free research files are added:
- `tools/research/local_l07_pwa_privacy_audit.py` for fail-closed static privacy contract checks; intended usage `python tools/research/local_l07_pwa_privacy_audit.py .`.
- `tests/test_local_l07_pwa_privacy_audit.py` with explicit negative cases for API and image cache poisoning, removed origin/GET/allowlist checks, dynamic cache.put, second fetch handler, browser downgrade, absent health/BEST paths and false live-test claims.

**Test evidence boundary:** the exact Python repository test suite above was added but **not executed** in this session. A separate source-level JS inspector was applied directly to the current GitHub file contents and **14/14 checks passed**, including allowed asset list, API/user-image exclusions, same-origin/GET/allowlist, shell-only cache writes, network-first handler, health/BEST/V2 and no-store/no-browser-fallback. This is not a live e2e or proof that all adversarial mutations are rejected by the static Python parser.

Remaining L07 true pre-release work: test a running LocalWorker `Origin`, Tailscale owner identity, preflight, unauthorized GETs and 429 lock behavior; Safari install/save/offline/online/abort/restore; Service Worker update and cache invalidation with real browser/OS; response headers and memory/cold startup. Do NOT sign off L07 from these read-only checks. No exact runtime SHA check or iPhone user acceptance performed. L02 research continues independently.

Security/quality non-promotion: user-supplied source pixels, private NPZ, canonical Phase4 owners and manual Golden unchanged; no generated visible pixels; no eyes/nose/mouth/brows drawn; Public/C08 and Local production untouched.
