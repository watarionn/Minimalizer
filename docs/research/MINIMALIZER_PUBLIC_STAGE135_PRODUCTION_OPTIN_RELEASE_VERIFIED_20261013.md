# MinimalizerPublic Stage135 owner-requested production opt-in release: VERIFIED

Date 2026-10-13 JST. The owner explicitly requested temporarily merging StructuralRecovery P0 and reflecting it in production.

## Main authority and exact scope
- StructuralRecovery P0 research PR **#390** merged to main at SHA `922b3e9118efb733b1f6d851e23c642a18595d09`. 172 **add-only** source-free research JS modules, tests, documents and research CI workflow; **no normal Public processing route, template or Local Minimalizer changed**. Its latest executable GitHub CI was **533 tests PASS / 0 fail / 0 skipped** at https://github.com/watarionn/Minimalizer/actions/runs/38285758605. Golden still HOLD.
- Owner-requested **standalone opt-in browser preview** PR **#391** merged at `163088822f17071ebf3e8f730166463e123a5b8c`. The new `web/static/structural-p0-stage135-preview.html` is isolated and links six P0 source-free ES modules. No existing standard converter script, HTML page, CSS, ONNX/WASM, Local Worker or Python service was modified.

## Verified HTTPS production deployment

**Live public page:** https://cf278796.cloudfree.jp/minimalizer/static/structural-p0-stage135-preview.html

Production host: existing Shin Free Server saved **FTPS** connection; remote directory `/cf278796.cloudfree.jp/public_html/minimalizer/static/`.

An independent, clean main checkout at exactly `163088822f17071ebf3e8f730166463e123a5b8c` passed `python scripts/build_shin_static.py`. Prior to any upload, **all seven target paths** returned HTTP 404. Published **six new source-free JavaScript modules FIRST, new opt-in HTML LAST** using binary FTPS PUT. No recursive mirror, file deletion or overwrite of existing site assets.

Seven published paths:
1. `structural-p0-stage135-preview.html`
2. `public-human-review-queue-p0.mjs`
3. `public-fullframe-review-p0.mjs`
4. `public-annotation-authority-p0.mjs`
5. `public-untrusted-fullscene-preview-p0.mjs`
6. `public-source-exact-rect-cover-p0.mjs`
7. `public-source-rgb-lossless-preview-p0.mjs`

All **7/7** were re-downloaded over actual live HTTPS and found **SHA256 byte-identical** to the verified main build. Content-Type: `text/html` for HTML and `application/javascript` for all `.mjs`. Existing five public runtime assets were saved before writing and downloaded again afterward: `index.html`, `static/app.js`, `static/browser-fallback.js`, `static/public-route.js`, `static/canonical-contour.js`. **5/5 old runtime SHA256 hashes identical before vs after.**

## Real Chrome over the ACTUAL HTTPS domain

Browser on real public HTTPS, no external upload: synthesized local-only **test fixture** PNG 64×64; drag-selected **720 actual test PNG opaque pixels**. The original-RGB single-palette preview exhibited **714 differing original RGB pixels / 4 rectangle vertices**; exact-original RGB preview exhibited **0 differing original RGB pixels / 2,880 explicit vertices**. Both SVG previews rendered. All network requests stayed on the production HTTPS host or same-origin browser blob URLs. Separate Chrome mobile viewport width 390px had document width 390px, **no horizontal overflow**. Desktop/mobile screenshots and the executable E2E replay are in the private project Drive deployment folder. This is NOT a physical iPhone Safari check.

No private GC001 or Raden original images, masks or Stage133 derived exact-RGB SVG were published. The visitor uploads PNG **only into their own browser**, manually selects a rectangle and sees source RGB observed from that file, not semantic person detection. Preview does not grant human Golden or new default conversion behavior.

## Rollback and hold status

For rollback, verify live SHA against the exact seven SHA-pinned new files in the Drive `STAGE135_LIVE_DEPLOY_VERIFIED.json` first, then remove **only the seven new paths** via FTPS and confirm 404. **Do not touch the normal converter assets.** Prepared, not executed. No need to revert main research commits merely to hide the isolated page.

P0 **whole-character Golden HOLD** remains: zero independently authenticated human semantic pixels, Stage8 GC001 3604>1887 and Raden 2370>1412 vertex-budget FAIL, no full-body anatomy/arm/sleeve/hair/neckwear Golden, no physical iPhone Safari and no exercised rollback. No misleading claim that the normal Public conversion has adopted Stage135 image quality.

Canonical artifacts: Google Drive `chatGPT及びCodex用/MinimalizerPublic/StructuralRecovery_P0_20261010/Stage135_PublicPreviewDeployment_20261013`: main-build asset SHAs, live HTTPS proofs, default-runtime byte-identical backups, desktop/mobile Chrome captures, non-destructive rollback list and published manifest.
