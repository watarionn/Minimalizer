# Minimalizer Local Compute Worker v1

## Purpose

Run the high-quality Minimalizer pipeline on the owner's Windows PC while keeping Railway as a fallback.

The local worker uses:

- rembg `u2netp` subject guidance
- RTMLib `balanced` structural guidance
- Layered Person enabled
- V2 deterministic primitive rendering
- no generative image model

The worker listens only on `127.0.0.1:28765`.

## Setup

From PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\setup_local_worker.ps1
```

The setup script creates the local venv, installs the web receiver dependencies, verifies the analysis dependencies, and installs the Windows login startup launcher.

## Start / stop

```powershell
.\scripts\start_local_worker.ps1
.\scripts\stop_local_worker.ps1
```

Health check:

```
http://127.0.0.1:28765/health
```

## Browser opt-in

The public Minimalizer site does not probe localhost by default.

On the owner's browser, open the production site once with:

```
https://minimalizer-web-production-a2bc.up.railway.app/?localWorker=1
```

This stores the local-worker opt-in in localStorage for that browser.

Chrome may ask for permission to access the loopback/local network. Allow it for the Minimalizer production origin. Chrome gates public-site to loopback requests behind Local Network Access permission. The browser waits long enough for this first-run permission interaction instead of immediately abandoning the loopback probe.

After opt-in:

1. Standard Minimalizer checks the local worker when the user starts minimalization.
2. If ready, the image is processed on the PC using rembg + RTMLib + Layered Person.
3. A successful local result is labeled `Minimalizer 2.0 Local · Local Worker · rembg+rtmlib`.
4. If the worker is unavailable or the browser denies local access, the request falls back to Railway and the UI explicitly labels the result `Railway fallback` with a permission/startup warning.

Do not infer that `?localWorker=1` alone proves local computation. The result metadata is the source of truth for the route actually used.

Disable local-worker routing for that browser with:

```
https://minimalizer-web-production-a2bc.up.railway.app/?localWorker=0
```

Color Strip remains on Railway.

## Mobile / remote access over Tailscale

The worker itself remains bound to `127.0.0.1:28765`. Remote access is provided by Tailscale Serve, so the worker is not opened on the home LAN or the public internet.

On the Windows PC:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_tailscale_mobile_worker.ps1
```

This adds a tailnet-only HTTPS proxy:

```
https://ywshtmr.tail8fd68c.ts.net:28765
  -> http://127.0.0.1:28765
```

Tailscale Funnel is not enabled for this Minimalizer port.

On the phone:

1. Open the Tailscale app and make sure it is connected to the same tailnet as the PC.
2. Open Chrome.
3. Open the production Minimalizer site once with:

```
https://minimalizer-web-production-a2bc.up.railway.app/?localWorker=tailscale
```

4. Choose an image and run Minimalizer normally.
5. Confirm the result metadata says `Minimalizer 2.0 Local · Tailscale Local Worker · rembg+rtmlib`.

The `tailscale` mode is stored in localStorage for that browser, so later visits can use the normal production URL while Tailscale remains connected.

If the phone is offline from Tailscale, the PC is offline, Tailscale Serve is unavailable, or the Local Worker is not ready, Minimalizer falls back to Railway and explicitly labels the result `Railway fallback`.

Remove only the Minimalizer Tailscale route with:

```powershell
.\scripts\uninstall_tailscale_mobile_worker.ps1
```

## Security boundary

- The Local Worker process stays bound to loopback only.
- PC-browser access uses `127.0.0.1:28765`.
- Mobile / remote access uses a Tailscale Serve HTTPS route that is tailnet-only.
- Minimalizer does not enable Tailscale Funnel for port `28765`.
- Browser Origin allowlist accepts the production Minimalizer origin and local development origins only.
- Unknown browser origins receive 403.
- One processing job at a time.
- No browser enterprise policy or administrator-level bypass is required.
