# Minimalizer Local / Public split (2026-10-08)

User-approved direction: **MinimalizerLocal** and **MinimalizerPublic** are separate pages, not a single LocalWorker-first page.

## Distribution

- **Public**: `web/static/index.html`, `web/static/public-route.js` and shared route-neutral `web/static/app.js`. Run `python scripts/build_shin_static.py`; publish `dist/shin` to the existing Minimalizer path on `cf278796.cloudfree.jp`. Minimalization goes directly to the Browser engine without touching a LocalWorker endpoint.
- **Local**: `local_worker/frontend/index.html` and `local_worker/frontend/local-route.js` plus PWA assets. The existing `local_worker.app` serves the UI at `http://127.0.0.1:28764/`; over the user's existing Tailscale Serve it is available via private HTTPS. The Local adapter uses same-origin ZeroBase2 BEST, then Local V2 if necessary, but no Browser downgrade.
- Image picker, result preview, downloads, Color Strip and responsive CSS remain shared UI. Local page/route are not copied by the static Public builder.

## Access and rollout

PWA installation is **not** authentication. Keep LocalWorker bound to loopback and Tailscale Serve strictly tailnet-only; do not enable Funnel or public port forwarding. Restrict Tailscale access to owner-authorized identities/devices. Set the private HTTPS Origin in the existing external `MINIMALIZER_LOCAL_ALLOWED_ORIGINS` configuration before mobile use. Public `cf278796.cloudfree.jp` is no longer a default allowed Origin after the new LocalWorker deploy; clear any obsolete external allowlist entry.

Important: deploy **Public first**, verify Browser direct processing, then update **Local** to remove the public origin. Deploy in reverse order would break the old live page. Preserve rollback artifacts.

Local service worker caches only the app shell. Never cache original images, rendered outputs, or API payloads.

## Gates

- `node --check` on shared/UI/route/SW JavaScript.
- `pytest tests/test_minimalizer_page_split.py tests/test_local_worker.py -q`.
- Browser smoke and Color Strip; Local ZeroBase2/V2 routing; Public build excludes private files.
- Owner PC and mobile PWA over private HTTPS; unauthorized Tailnet user and public site cannot reach LocalWorker.
- Exact live URLs and rollout state verified after deployment.

No pyfreeform package is installed by this split. The GPL and visual-style PoC are separate next-stage research.

## Tailnet owner gate (hardening)

The private LocalWorker also checks the Tailscale Serve `Tailscale-User-Login`
header against one owner login, configured **outside the repository** in
`%LOCALAPPDATA%\\Minimalizer\\config\\owner-login.txt` or via
`MINIMALIZER_LOCAL_OWNER_LOGIN`. Unconfigured remote access fails closed.
Loopback-only direct requests remain available for local administration.
The worker must remain bound to `127.0.0.1:28764`; the Tailscale HTTP
reverse proxy removes spoofed Tailscale identity headers. Tailnet access
policy/grants should additionally restrict TCP 28765 to the owner.

The worker needs the Tailscale HTTPS PWA origin allowlisted using existing
external `MINIMALIZER_LOCAL_ALLOWED_ORIGINS` config. Do not put owner login,
API keys, cookie material, or personal tailnet configuration into GitHub.

## Owner Local PWA exemption from RRM global admission (2026-10-08)

The authenticated MinimalizerLocal PWA has a user-approved exception from
Rinka Resource Manager's global heavy-compute slot and the 6 GiB free-RAM
admission threshold. Both LocalWorker HTTP image routes
(`/api/zerobase2/minimalize` and `/api/v2/minimalize`) run without importing
or acquiring `local_worker.rrm_admission.compute_slot`.

This exemption does **not** disable LocalWorker's `_process_lock`, so only
one image computation runs at a time; a concurrent request may still return
429 `Local Minimalizer worker is busy.`. Errors due to real memory exhaustion
or pipeline faults can still occur; this is not a RAM reservation.

No RRM project state, global thresholds, queued/running leases, or other
projects are changed. The standalone opt-in `rrm_admission` helper remains
available for unrelated future non-PWA batch calls. This behavior is code-level
and survives LocalWorker restarts without a special environment variable.
