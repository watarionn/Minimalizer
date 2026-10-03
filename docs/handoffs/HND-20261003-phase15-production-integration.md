# HND-20261003 Phase 15 Production Integration

Status: DEPLOY PENDING

Phase 15 production integration is merged to main at `fb18a5516b8c93a9ff5a5a98fb89e01a1b70ced8`. ZeroBase2 has a fail-closed Local Worker endpoint and an opt-in Web UI route. Development/production consistency and direct production API smoke pass. The legacy route is retained for rollback. The Shin static package has been rebuilt from this main head and its `static/app.js` hash matches the source app.js.

Do not close migration from the earlier Browser Fallback v12 smoke. It proved the current public UI works but did not prove ZeroBase2 routing.

Live production verification on 2026-10-03 shows the public `static/app.js` is still the previous Browser Fallback v12 build and does not contain the `engine=zerobase2` wiring. GitHub main is therefore ahead of Shin production.\n\nNext action: upload the already-built `dist/shin` package to the existing Shin Free Server document root `public_html/minimalizer` using the established deployment session, then run a real-Chrome standard-button smoke using `?engine=zerobase2&localWorker=1`. Close migration only when browser evidence identifies the ZeroBase2 route and the visible result label reads `Minimalizer ZeroBase2`.

Runtime lesson: use the Python 3.11 worker runtime; setup must install the full local-worker requirements. Never infer runtime compatibility from an existing venv directory.
