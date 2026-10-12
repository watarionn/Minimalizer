# MinimalizerPublic P0 Stage135: owner-requested merged research and safe optional public preview

Date 2026-10-13 JST. Owner explicitly requested temporary merge and production reflection of Draft PR #390. PR #390 **merged into main at 922b3e9118efb733b1f6d851e23c642a18595d09**. The whole-character StructuralRecovery P0 Golden HOLD and Stage8 vertex caps are still NOT satisfied. Merging source-only tests/modules cannot improve ordinary Public's image conversion by itself.

## Safe production release boundary

Add ONLY opt-in, standalone `web/static/structural-p0-stage135-preview.html`, with direct relative dynamic ES imports of:
- `public-human-review-queue-p0.mjs`
- `public-fullframe-review-p0.mjs`
- `public-annotation-authority-p0.mjs`
- `public-untrusted-fullscene-preview-p0.mjs`
- `public-source-exact-rect-cover-p0.mjs`
- `public-source-rgb-lossless-preview-p0.mjs`

All are source-free research JS and none was imported into `web/static/index.html`, `public-route.js`, `browser-fallback.js`, `app.js` or Local Minimalizer. Do NOT upload PRIVATE Stage133 SVGs, original RGBA, private Golden screenshot or historical mask bytes. Do NOT upload the entire `dist/shin` as recursive sync, edit remote `.htaccess`, modify ONNX/WASM, LocalWorker, or user-accessible default converter assets.

The standalone page lets an interested visitor select a **local PNG** (maximum 340x340, no network upload), manually drag a **rectangular ROI** (at most 20,000 original opaque pixels), compare original-sampled single RGB against exact per-pixel original RGB source-only candidate SVG, and see explicit differing source RGB pixels, SVG bytes and true rectangle vertices. No automatic body/hair/sleeve classification, no source-missing pixels, no generative fills. Preview caseId `GC001` is an internal validator compatibility value for an arbitrary uploaded PNG, **not** an identity claim about the real GC001 source. Zero masks explicitly mean unknown semantic meaning. No human Golden promotion. The selection step deliberately takes only decoded source alpha255 pixels.

Local Chrome test: isolated HTTP at localhost, synthetic TEST original PNG generated in browser, 720 manually selected opaque original pixels; one-source-color preview 714 source RGB differences / 4 rectangle vertices, exact original RGB preview **0 source RGB differences / 2,880 rectangle vertices**. Both returned valid displayable SVGs, and all network requests stayed on local origin / blob URL, no image upload.

Publish to verified Shin Free Server via saved WinSCP FTPS session `cf278796@sv210.cloudfree.ne.jp`, target `/cf278796.cloudfree.jp/public_html/minimalizer/static/`. Upload new JS modules first and HTML **last**; binary mode, no other file overwrite, no recursive synchronization or deletions. Before and after verify live SHA256 for the original `index.html`, `public-route.js`, `browser-fallback.js`, `app.js` and `canonical-contour.js`. Validate 7 newly uploaded asset hashes over real HTTPS and Chrome on actual public host. Save every hash and exact upload inventory for safe rollback. Rollback consists of removing only these 7 NEW paths; normal converter must remain untouched.

Product Golden remains HOLD: historic full-character scene vertex failures GC001 3604>1887 / Raden 2370>1412, 0 independently verified human semantic pixels, missing hand/skin/sleeve/hair/neckwear shape Golden, physical iPhone Safari HTTPS and rollback not exercised. Opt-in public metric tool is **not** the finalized new converter, and cannot be represented as all algorithms passing quality gates.
