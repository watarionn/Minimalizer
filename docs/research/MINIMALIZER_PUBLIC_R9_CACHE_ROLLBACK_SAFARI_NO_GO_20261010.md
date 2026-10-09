# MinimalizerPublic R9 | Static cache and rollback verification

2026-10-10. **R9 engineering PASS; production release NO-GO.**

## Actual source and scope

R9 is research stacked on R8 Draft #361, R7 #360, R6 #359 and earlier Public R1–R5. No Local Minimalizer/Worker changes, main merge, production deploy, image conversion, new facial details or Golden approval.

Source deployment documentation `docs/WEB_DEPLOYMENT.md` names Shin Free Server and `python scripts/build_shin_static.py` producing `dist/shin`. The current HTML uses unversioned `static/styles.css` and a fixed `static/app.js?v=20261008-local-public` query. Neither is a new content fingerprint per deployment. No Public Service Worker registration was found in the tested source and browser context. **Real production HTTP response headers were NOT checked.**

## Genuine Chrome simulated deployment

`scripts/verify_public_r9_cache_rollback.py` consumes actual canonical R6 NO_GO and R8 legal-HOLD JSON, refuses forged release admission, calls the real static builder into a disposable directory and creates three isolated static trees: byte-identical baseline, test-only canary (only index.html / app.js / styles.css have appended comments), and byte-identical recovery. All **68 build files** are compared at SHA-256 file precision. No test data enters a product or public host.

On a localhost server, **hypothetical** cache headers were set: HTML `no-store`, static assets `max-age=3600`. Actual desktop Chrome 154.0.8037.98 with real browser cache exercised four paths: `index.html`, `app.js?v=20261008-local-public`, `styles.css`, vendored resvg `index_bg.wasm`.

| Tested condition | Result |
|---|---|
| Original and restored full static tree | 68/68 SHA-identical |
| Fresh browser fetch during canary and restored release | 4/4 exact in each |
| Default browser cache after switching to canary | 2 stale routes |
| Default browser cache after restoring baseline | 2 stale routes |
| Unique new build query on each tested URL | exact expected bytes |
| Browser Service Worker registrations in isolated origin | 0 |
| Real iPhone Safari tested | NO |
| Actual Shin/CDN cache headers tested | NO |

The two stale paths in both directions were **app.js** and **styles.css**. This is a simulated-cache hazard, **not a verified current production incident**.

Regression: **84 Python tests PASS**, Python compile PASS. Two independent real Chrome runs produced an **identical JSON file**, SHA-256 `55c937e428568f333ae77642785dbead9dd5c2b4817e706c54a850c070d7aab5`.

## Proposed Public-only rollout/recovery runbook (NOT executed)

1. Before any real deploy, preserve an immutable full SHA manifest and byte-exact snapshot of the **entire** previous static release, source commit, and recorded origin. Never assume a hosting atomic rename or CDN cache purge exists.
2. Build a candidate using a **distinct release identity for every changed JS, CSS, dynamic import, model or WASM asset** and the HTML references to them. A new index.html alone cannot prevent cached assets from mixing. Keep old versioned assets until cached pages age out.
3. Check **actual host** caching headers, ETag, query cache-key handling, Service Workers, browsers with warmed caches and stale tabs. Only evidence from the real HTTPS origin can approve the deployment step.
4. Require original source and Golden human signoff, arm/tie/staff semantic review, Stage8 original ring budget, resvg DPR2 cross-renderer parity, license-source compliance and physical Safari/iPhone DPR evidence.
5. If approved for live switching, use only a provider-supported reversible full-release cutover. On incident, switch back the **whole saved build**, verify warm and fresh browser file hashes for HTML/JS/CSS/WASM, revalidate caches where supported, record owner and timestamps, and separately verify Local Worker is unaffected.
6. If the host does not support an atomic/reversible switch, **HOLD** and design an alternate provider-specific recovery plan rather than assuming per-file overwrite is safe.

## Physical iPhone Safari checklist (UNSIGNED)

Real device model, iOS/Safari versions, public URL and deployed commit, devicePixelRatio, viewport, uncached and warmed-tab loading, asset cache identity, mobile original-source / Golden visual checks, network-loss recovery, actual release rollback and resulting screenshots/SHAs must be captured **on a physical iPhone**. R9 is desktop Chrome only, reported DPR1. No Safari pass or person-specific semantic part ownership is claimed.

## Decision

`status=CACHE_SIMULATION_VERIFIED_PRODUCTION_NO_GO`, `releaseAuthorized=false`, `fullProductionRollbackSigned=false`, `iphoneSafariDprSigned=false`, `mergeOrDeployPerformed=false`. R6's eight release blockers remain blocked. No production merge/deploy. Next R10: research-only Public content-fingerprinted static asset manifest and browser verification, subject to identical product/Local isolation and no new pixels.
