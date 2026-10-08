# MinimalizerLocal Origin error recovery: controller environment snapshot (2026-10-08 JST)

**Status: live private HTTPS fix verified.** Applies to the separate MinimalizerLocal PWA release after the Local/Public page split, not to the public Browser-only Minimalizer page.

## Symptom and evidence

Owner reported **"Origin is not allowed"** opening/using MinimalizerLocal at its private Tailscale Serve HTTPS endpoint. The backend error text matches the explicit `guard_browser_origin` 403 response in `local_worker/app.py`.

An isolated live probe showed:
- `GET /health` without an Origin header: HTTP **200**, LocalWorker `ready`, ZeroBase2 active.
- `GET /health` with `Origin: https://ywshtmr.tail8fd68c.ts.net:28765`: HTTP **403** both through loopback and private Tailscale Serve HTTPS.
- The external config file `%LOCALAPPDATA%\Minimalizer\config\public-origin.txt` already contained the exact private HTTPS Origin.
- The persistent user-session supervisor `%LOCALAPPDATA%\Minimalizer\start-production-worker.ps1` reads `public-origin.txt` **once on controller startup**, sets `MINIMALIZER_LOCAL_ALLOWED_ORIGINS` then loops restarting the Uvicorn child. The external origin configuration was written *after* this controller started, so the child inherited the controller's earlier environment snapshot even on later child restarts. The source-level allowed-origin tuple is also generated when the Python worker module imports.

The incident was therefore a **stale startup configuration**, **not** an unavailable Worker, invalid HTTPS proxy, or need to allow the public Cloudfree Origin.

## Exact scoped recovery

1. Verified the source config file had the private Tailscale Serve Origin. Verified the **single** loopback listener on `127.0.0.1:28764`, its Uvicorn parent process, and the parent supervisor command line pointed to `start-production-worker.ps1`. This identity check prevents stopping other processes.
2. Terminated **only** that verified Minimalizer controller process tree, including its matching Worker children, with the Windows process-tree termination command. Tailscale Serve and all unrelated AI services were left untouched.
3. Relaunched the existing controller from the user-profile `start-production-worker.ps1`. Its new invocation read the saved Origin config before starting Uvicorn. Did not change the remote HTTPS route, security policy, repository code, or unrelated services.
4. Repeated private HTTPS tests.

## Post-recovery checks (real endpoints)

| Probe | Observed |
| --- | --- |
| `GET /health` with **private Tailscale Origin** over private HTTPS | HTTP **200** |
| `Access-Control-Allow-Origin` | Exact private HTTPS Origin |
| `GET /` private PWA | HTTP **200** |
| Worker `status` / active route | `ready` / `zerobase2` |
| `OPTIONS /api/zerobase2/minimalize` with private Origin, request method POST | HTTP **200**, exact CORS Origin |
| `POST /api/zerobase2/minimalize` with private Origin but deliberately missing image | HTTP **422** (input validation, **not** Origin 403); no full generation performed |
| `GET /health` with Cloudfree public Origin or unrelated Origin | HTTP **403**, remains denied |

All reported checks refer to actually issued requests. A complete real-image generation and mobile PWA UI flow were **not** repeated in this incident check.

## Cause, impact, correction, prevention

- **Cause:** Updating `public-origin.txt` without restarting the *supervisor* left `MINIMALIZER_LOCAL_ALLOWED_ORIGINS` stale. Restarting only Uvicorn children is insufficient because each inherits the supervisor's startup environment.
- **Impact:** Local PWA same-Origin image API / health checks received 403 despite a healthy, reachable worker. Public-only browser route was unaffected.
- **Correction:** Re-read config by verified, targeted supervisor restart; confirm allowlisted private Origin and exact CORS header. Preserve rejection of public/untrusted origins.
- **Prevention:** When changing `public-origin.txt` or other startup-scoped Worker settings, include a **targeted supervisor restart** as an explicit deployment step. Validate private HTTPS **with the real Origin header**, not only a no-Origin `GET /health`. Also verify POST OPTIONS / validation-path behavior. Do not conclude success from a 200 no-Origin health response alone.
- **Scope safety:** Keep Tailscale Serve tailnet-only on port 28765, Worker loopback-only on 28764 and owner identity gate enabled. Do not enable public exposure, add the public Cloudfree Origin, modify Chrome security settings or kill unrelated services.
- **Follow-up hardening candidate:** A future separate review can make allowed-Origin config dynamically reloadable or provide a guarded controller restart helper. Neither behavior is claimed implemented by this incident recovery.

## Related source

- `docs/MINIMALIZER_LOCAL_PUBLIC_SPLIT_20261008.md`
- `docs/handoffs/HND-20261008-LOCAL-WORKER-CONNECTION-RECOVERY.md`
- `local_worker/app.py`, `tests/test_local_worker.py`
