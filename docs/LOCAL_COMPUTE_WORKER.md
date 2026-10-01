# Minimalizer Local Compute Worker v1

## Purpose

Run the high-quality Minimalizer pipeline on the owner's Windows PC while the public site itself remains static-hostable.

The production routing contract after Browser Fallback v12 is:

1. owner browser with Local Worker opt-in -> Local Worker
2. if Local Worker is unavailable -> Browser Fallback v12
3. browsers without Local Worker opt-in -> Browser Fallback v12

Railway is not part of this runtime fallback chain.

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

## Configure the public static origin

Before switching the public frontend to its final HTTPS origin, save that origin outside the repository:

```powershell
.\scripts\set_local_worker_origin.ps1 -Origin "https://example.invalid"
```

Replace the placeholder with the actual production origin. The value is stored in:

```text
%LOCALAPPDATA%\Minimalizer\config\public-origin.txt
```

`start_local_worker.ps1` loads this file into `MINIMALIZER_LOCAL_ALLOWED_ORIGINS` when the worker starts. Restart the worker after changing the origin.

Do not commit the machine-specific production origin to the repository.

## Start / stop

```powershell
.\scripts\start_local_worker.ps1
.\scripts\stop_local_worker.ps1
```

Health check:

```text
http://127.0.0.1:28765/health
```

## Owner browser opt-in

The public site does not probe localhost unless that browser has opted into Local Worker routing.

Open the final production site once with:

```text
https://<production-origin>/?localWorker=1
```

This stores the loopback Local Worker preference in localStorage. Chrome may request permission for local-network access. Allow it for the Minimalizer production origin.

After opt-in:

1. Minimalizer probes the Local Worker when minimalization starts.
2. When ready, the image is processed on the PC with the high-quality Local Worker pipeline.
3. If the worker is unavailable or browser access is denied, Browser Fallback v12 processes the image locally in the browser.
4. Color Strip is also self-hosted in the browser runtime.

Disable Local Worker routing for that browser with:

```text
https://<production-origin>/?localWorker=0
```

Browser Fallback v12 remains available.

## Browser Fallback controls

Browser Fallback is enabled by default.

Useful query parameters:

```text
?browserFallback=force
?browserFallbackQuality=exact
?browserFallbackQuality=lite
```

`force` bypasses Local Worker for testing. The quality setting is persisted in localStorage.

## Mobile / remote access over Tailscale

The worker itself remains bound to `127.0.0.1:28765`. Remote access is provided by Tailscale Serve, so the worker is not opened on the home LAN or public internet.

On the Windows PC:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_tailscale_mobile_worker.ps1
```

This adds the tailnet-only HTTPS proxy:

```text
https://ywshtmr.tail8fd68c.ts.net:28765
  -> http://127.0.0.1:28765
```

Tailscale Funnel is not enabled for this port.

On the phone, connect Tailscale and open:

```text
https://<production-origin>/?localWorker=tailscale
```

If Tailscale, the PC, Tailscale Serve, or Local Worker is unavailable, Browser Fallback v12 is used instead.

Remove only the Minimalizer Tailscale route with:

```powershell
.\scripts\uninstall_tailscale_mobile_worker.ps1
```

## Static frontend package

Build the Shin Free Server document root with:

```powershell
python scripts\build_shin_static.py
```

Output:

```text
dist\shin\
  index.html
  static\
    models\u2netp.onnx
    vendor\onnxruntime\...
    ...
```

The builder rejects hosted API / Railway runtime markers and copies nested model/runtime assets required by Browser Subject guidance.

## Security boundary

- Local Worker stays bound to loopback only.
- PC-browser access uses `127.0.0.1:28765`.
- Mobile access uses tailnet-only Tailscale Serve.
- Tailscale Funnel is not enabled for the Minimalizer worker port.
- The public HTTPS origin is stored outside the repository and applied to the CORS allowlist at worker startup.
- Unknown browser origins receive 403.
- One Local Worker processing job runs at a time.
- Browser Fallback v12 requires no hosted image-processing API.
