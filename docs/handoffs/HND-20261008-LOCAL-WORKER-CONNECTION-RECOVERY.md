# Local Worker connection recovery: startup script, port, Chrome Local Network Access

Date: 2026-10-08 JST. Canonical repository `watarionn/Minimalizer`, `main`.

## Incident

Owner reported: "localworkerに接続できない" immediately after research PR #223 merge and an opt-in SA10.41 public preview deployment.

**The PR #223 merge and research preview were not the cause**: public `index.html`, `app.js`, `browser-fallback.js`, `canonical-contour.js`, `browser-subject.js` remained SHA256-identical before and after that deployment. Local Worker runs on the PC, with separate network and startup behavior.

Independent verification showed:
1. Public site's `web/static/app.js` expects **loopback `http://127.0.0.1:28764`** on PC and **tailnet-only `https://ywshtmr.tail8fd68c.ts.net:28765`** on mobile.
2. Existing Tailscale Serve was correctly set up: HTTPS **28765** forwards to HTTP **127.0.0.1:28764**.
3. The worker was **not listening on port 28764**, giving local connection-refused and Tailscale HTTP **502**.
4. Windows Startup shortcut `Minimalizer Local Worker.cmd` pointed to `%LOCALAPPDATA%\Minimalizer\start-production-worker.ps1`, **which no longer existed**.
5. The developer working checkout `C:\Work\Projects\Minimalizer` was still on old feature branch `feature/zerobase2-phase12-style-constraint-simplification` (HEAD `2883e7e...`); its old `scripts/start_local_worker.ps1` used **28765 as the Worker listening port**, whereas modern public app.js and Tailscale Serve require **28764**.
6. That older feature checkout's `local_worker/app.py` also lacked `allow_private_network=True` in CORS middleware, though current GitHub `main` contains it. In tests its private-network preflight returned HTTP 400.
7. Chrome 154 now *additionally* enforces user-granted **Local Network Access (LNA)** permissions, independently of CORS/PNA preflights. In a fresh isolated headless browser profile, requests to loopback and Tailnet were initially denied by LNA. These permissions must be accepted **per user's actual browser/site profile** and must never be force-enabled in the user's Chrome on their behalf.

## Authorized repairs performed

- Preserved pre-repair Startup launchers and previous controller for rollback.
- Cloned GitHub **main** into a dedicated clean/unchanged local execution checkout `C:\Work\Projects\MinimalizerProductionWorker`, verified HEAD **`9b3b3c633fd5bddd33dd25e781aa21c3b1d7c046`** and clean worktree. This is a deployable clone of GitHub's canonical source, **not a new local source of truth**.
- Reused existing verified CPython 3.11 environment `C:\Work\Projects\Minimalizer\.venv311\Scripts\python.exe` without installing libraries or modifying the owner's dirty feature worktree. FastAPI/Starlette accept the required LNA/CORS flags.
- Created a user-profile-only startup/controller under `%LOCALAPPDATA%\Minimalizer\start-production-worker.ps1` that runs `uvicorn local_worker.app:app --host 127.0.0.1 --port 28764 --workers 1` using the clean production source checkout. It serializes competing monitor launches via a named user-session mutex, logs locally, sleeps and retries on unexpected process exit. Existing user-configured origin allowlist file is honored if present; no secrets/config were overwritten. The source app's default CORS includes `https://cf278796.cloudfree.jp`.
- Windows login Startup shortcut `Minimalizer Local Worker.cmd` now refers to the **existing** profile controller. This is a login-triggered service and an internal crash-retry loop, not a Windows system-boot service.
- Stopped only the explicitly identified obsolete localhost:28765 Worker process, and then the obsolete localhost:28764 old-feature-code process while switching to the canonical main checkout. Left Tailscale, unrelated servers, ComfyUI, and owner's uncommitted developer files untouched.
- Confirmed no remaining localhost `127.0.0.1:28765` listener; the Tailscale frontend on tailnet interface `:28765` remains active as designed.

## Final tests

- `http://127.0.0.1:28764/health`: **HTTP 200**, `worker=local-compute-v1`, `ready=true`, `active_production_route=zerobase2`, `zerobase2_authorized=true`.
- `https://ywshtmr.tail8fd68c.ts.net:28765/health`: **HTTP 200** with the same Worker/ready/ZeroBase2 status.
- `OPTIONS /health` from `Origin: https://cf278796.cloudfree.jp` and `Access-Control-Request-Private-Network: true`: **HTTP 200**, `Access-Control-Allow-Origin` matches exact public site, `Access-Control-Allow-Private-Network: true`.
- Actual **Chrome 154** on real public origin `https://cf278796.cloudfree.jp/minimalizer/`: a fresh isolated headless profile **without LNA permissions** fails with `Permission was denied ... loopback/local address space`. This is expected Chrome security behavior and not a worker failure.
- Actual **Chrome 154** in a separate disposable profile, **after simulated explicit site user grant** via DevTools `Browser.grantPermissions` of `loopbackNetwork` + `localNetwork`: `navigator.permissions.query` both `granted`, browser `fetch()` to both endpoints **HTTP 200 + ready=true + zerobase2 authorized**. Public site's own `probeLocalWorker()` returns **ready=true mode=loopback** for desktop, **ready=true mode=tailscale** under mobile UA emulation. No browser-security-bypass flags, no change to owner's actual Chrome settings.
- Main worker Python import and Chrome PNA test pass; current worker process is persistent and monitored. **Full arbitrary-input high-quality image-generation POST was not separately tested**.

## Required end-user browser action

From the real user's Chrome (not the disposable test profile):
1. Open **https://cf278796.cloudfree.jp/minimalizer/**.
2. If Chrome asks to find or connect to devices on local network, click **Allow** for this trusted Minimalizer site.
3. If the popup was previously blocked: site information icon left of the address bar → **Site settings**. Set **Apps on device / デバイス上のアプリ (`loopback-network`)** to **Allow** for PC localhost. Set **Local Network (`local-network`)** to **Allow** when using the Tailscale route. Reload the tab, retry. Wording varies by Chrome version.
4. For mobile, also connect the Tailscale client to the same tailnet, and grant browser/OS local network permission if prompted.

**Never globally disable Chrome's Local Network Access or web security to bypass this per-site permission.** Source: Chrome LNA security model and Chrome Site Settings docs.

## Preservation / rollback

Evidence and runtime-controller backup under Google Drive **`chatGPT及びCodex用/Minimalizer/LocalWorker_Recovery_20261008`**. The user-profile supervisor is a generated workstation-local operational launcher; canonical code remains GitHub `main`. When updating production code, create/validate a fresh GitHub deployment checkout and restart the worker in the normal guarded manner. Avoid repointing Startup at the dirty feature checkout; that caused the wrong port drift.

Rollback: restore a previously saved Startup launcher and old worker controller from Drive, but this will reintroduce the 28764/28765 mismatch. Prefer using the fixed controller or rebuilding it from this handoff and GitHub main.

**Decision: worker backend, both network routes, ZeroBase2 authorization, and site-origin browser connection with explicitly granted LNA all PASS. User's own browser site permission still requires their approval.**
