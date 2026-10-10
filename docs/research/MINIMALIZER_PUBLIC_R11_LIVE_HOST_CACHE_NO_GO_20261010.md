# MinimalizerPublic R11: real hosting cache and held release admission

2026-10-10 | **Real host read-only audit PASS / production release NO-GO.**

## Context and boundaries

This is R11 research stacked on R10 Draft PR #370, R9 #364, R8 #361, R7 #360, R6 #359 and earlier Public R1–R5 Draft. Separate v34 Draft #308 remains HOLD.

The actual Public HTTPS URL is grounded by `docs/BROWSER_FALLBACK_V12.md` and archived production handoffs: `https://cf278796.cloudfree.jp/minimalizer/`. The host was queried solely by HTTPS **GET and HEAD**, with bounded reads; no credentials, server admin panel access, FTP write, cache purge, deployment, GitHub merge, Local Minimalizer/Worker manipulation or image conversion on the live host.

The built research R10 versioning scheme was **not uploaded** to this site.

## Real host measurements, two independent identical reads

| Existing host resource | HTTP | Cache-Control | Other observed state |
|---|---:|---|---|
| `/minimalizer/` | 200 | no explicit header | HTML has 14 `static/` CSS/JS references and fixed Public app/route query |
| `static/styles.css` | 200 | `max-age=604800` | CSS is loaded from a stable URL |
| `static/app.js?v=20261008-local-public` | 200 | `max-age=604800` | fixed query identifier despite file content changes being possible |
| `static/public-route.js?v=20261008-local-public` | 200 | `max-age=604800` | fixed query identifier |
| `static/browser-subject.js` | 200 | `max-age=604800` | 13,554 bytes reported |
| `static/models/u2netp.onnx` | 200 | no explicit header | 4,574,861 bytes reported by HEAD only; no 4.6 MB model download |
| `static/vendor/resvg-wasm/index_bg.wasm` | 404 | no explicit header | optional R4 research WASM **not deployed**, not a failure of existing Public route |

The 604,800-second max-age is **7 days**, based on the real hosting response, not an R9 hypothetical header. Browsers that cached a stable URL can therefore retain outdated scripts or CSS for a long time if these files are overwritten in place. This is a **confirmed unsafe update condition**, not proof that any current user is experiencing a stale-cache incident.

The actual live HTML has 14 `static/` script/style links versus the 24 R10 research references. App and CSS SHA match the archived research input snapshot, while the live route JS is not the research R10 adapter. This is expected while research plugins are not deployed. Therefore **never publish R10 folder assets by simply overwriting the existing root files**.

## R11 implementation

- `scripts/verify_public_r11_live_host.py` is a read-only same-origin HTTPS probe. Only preselected `/minimalizer/` public routes can be requested; redirects are constrained to the same origin/path, body reads are capped at 320 KB and model/WASM are HEAD-only.
- Verifies real R6/R8/R9/R10 canonical evidence SHA chain and NO-GO states **before** network actions. The archived R10 source-side release proof must include 66 assets and actual Chrome byte-parity.
- Records status, path, content-type, cache-control max-age, ETag, Last-Modified, bounded body SHA, and boolean Expires presence; intentionally omits volatile Date/Expires values so independent runs can be compared reproducibly.
- Fails on missing **core** Public routes. Optional resvg-WASM 404 remains a separate explicit `optionalResvgNotPresentIsNotProductOutage=true` assessment.
- Records true live `legacyCssFixedUrlDetected`, `legacyAppFixedQueryDetected`, `liveAssetReuseCacheRisk`, and leaves host atomic release switching, cache-purge support, versioned assets on the live host and genuine rollback **unverified**.
- Fail-closed result: `status=LIVE_HOST_HTTP_AUDIT_PASS_RELEASE_NO_GO`, `releaseAuthorized=false`, `liveServerFileWrites=0`, `mergeOrDeployPerformed=false`.

## Test and repeatability evidence

- Seven added R11 tests: same-origin/GET-HEAD security guard, cache parser, HTML reference enumeration, optional 404 isolation, core 404 fail-closed, forged R10 release denial, no-overwrite/Local-Public isolation.
- Full R1–R11 + Local/Public regression: **98 Python tests PASS**. Syntax compilation PASS.
- Two independent real-host runs produced **byte-identical 6,125-byte audit JSON**, SHA-256 `47d4352ebd2f274d0e46c1800e9dd32a060681eccd2dfb787fd8a94c59522780`.
- Evidence and report must be saved within `chatGPT及びCodex用/MinimalizerPublic/LibraryConvergence_R11_20261010` and read back before calling preservation complete.

## Release decision and next stage

**R11 engineering complete; the R6 eight release blockers remain unresolved.** R11 verified actual cache behavior and current resource availability, but did NOT establish that the hosting provider supports an atomic directory switch, preservation of multiple releases or dependable cache invalidation. These must be proven with a host-supported, explicitly approved non-production staging mechanism before deployment.

The resvg DPR2 full-scene mismatch, original Stage8 contour/vertex budget, semantic source ownership and protected arms/tie/staff/face rules, human original/Golden review, real iPhone Safari, MPL-2.0 redistribution review and real rollback approval all stay NO-GO.

Next proposed R12 prioritizes the **source-authenticated original Stage8 contour/vertex budget** instead of more release plumbing, with no guessed semantic parts or new pixels; preserve independent manual and device gates.
