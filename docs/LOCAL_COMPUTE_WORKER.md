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

Chrome may ask for permission to access the loopback/local network. Allow it for the Minimalizer production origin. Chrome gates public-site to loopback requests behind Local Network Access permission.

After opt-in:

1. Standard Minimalizer checks the local worker.
2. If ready, the image is processed on the PC using rembg + RTMLib + Layered Person.
3. If the worker is unavailable or the browser denies local access, the request falls back to Railway.

Disable local-worker routing for that browser with:

```
https://minimalizer-web-production-a2bc.up.railway.app/?localWorker=0
```

Color Strip remains on Railway.

## Security boundary

- Bound to loopback only, not LAN/WAN.
- Browser Origin allowlist accepts the production Minimalizer origin and local development origins only.
- Unknown browser origins receive 403.
- One processing job at a time.
- No browser enterprise policy or administrator-level bypass is required.
