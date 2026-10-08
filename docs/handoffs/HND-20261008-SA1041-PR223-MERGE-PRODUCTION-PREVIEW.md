# HND-20261008: PR #223 user-approved merge and SA10.41 production research preview

**Status 2026-10-08 JST: GitHub MERGED; research preview SHIPPED to public Shin Free Server; default conversion unchanged.**

## User approval and exact scope

The owner requested "一旦マージして本番反映して！私も本番環境で確認する". This **explicitly supersedes the earlier draft PR's "do not merge until final quality PASS" decision** for preservation and an **opt-in research preview**, but does not convert failed pixel/arm/vertex acceptance tests into PASS.

- Research PR: [watarionn/Minimalizer #223](https://github.com/watarionn/Minimalizer/pull/223).
- Research merged into `main`: **`10b5929b936cccb6f3ea5348a88d02087cf41356`**.
- PR head included SA10.32 through SA10.41 research Python modules, tests, JSON evidence and reports. It did **not** contain production `web/static` converter changes.
- Independently built `main` with the standalone preview page commit **`5d423f8b7dc5a851e39c2edf78c725fdab569360`**, using `scripts/build_shin_static.py` and publishing its new `web/static/sa1041-preview.html`.
- Public product site: **https://cf278796.cloudfree.jp/minimalizer/**.
- **Public, Chrome-rendered, read-only SA10.41 comparison:** **https://cf278796.cloudfree.jp/minimalizer/static/sa1041-preview.html**.

## What this user can actually inspect

The new public preview renders two source-attested vector SVGs inside the actual visitor's browser, next to their signed source/OpenCV reference images and pixel difference maps:
- **GC001 / Kyoko**: 11 original owner primitives, three Phase9 interior source-observed color planes and five Stage37 apparel polygons (two navy, two white, thin green tie). Full-scene browser/source reference difference: **3,919 RGB pixels**. Face 140, left arm 206, right arm 199 source-protected-mask pixels differ.
- **Juufuutei-Raden**: 11 owner primitives, one Phase9 interior plane, **zero mismatched outfit overlays**. Full-scene browser/source difference **2,681 RGB pixels**; protected face 122, left arm 237, right arm 255 pixels differ.
- **Original global source geometry vertex cap FAIL:** GC001 3,604 > 1,887; Raden 2,370 > 1,412. Additional SVG masks and color shapes count honestly (4,312 / 2,976 combined source vertex occurrences).
- The original saved full-character OpenCV images are correctly reconstructed pixel-exact; it is the vector SVG browser rendering that is **NOT** pixel-exact.
- No original source input PNG or generative image is publicly embedded as a fake SVG render.
- The read-only preview is **not an image upload+conversion service**. Existing browser-only and optional Local Worker conversion still use their preexisting implementations; SA10.41 Python research cannot be activated as default static-browser JS without a separately engineered integration. Users testing arbitrary uploads will not see SA10.41 rendering.

## Safe deployment details

Actual target: Shin Free Server FTPS saved session, document root `/cf278796.cloudfree.jp/public_html/minimalizer/static/`.

Deploy was **new files only**:
1. `sa1041-preview.html` from the **fresh verified GitHub main build**.
2. `sa1041-preview/gc001.svg`, `gc001-reference.png`, `gc001-diff.png`.
3. `sa1041-preview/raden.svg`, `raden-reference.png`, `raden-diff.png`.

Binary visuals originate from original evidence in `chatGPT及びCodex用/Minimalizer/SA1041_FullCharacterSVG_20261008`, and are reproduced and hash-verified. The original input source PNGs were NOT published; only the research-generated vector outputs and source-faithful simplified comparison images.

- **Fresh clone and static build:** `main` exactly `5d423f8`; `dist/shin` built.
- **Before publishing**, independently fetched five actual public production runtime assets: `index.html`, `app.js`, `browser-fallback.js`, `canonical-contour.js`, and `browser-subject.js`. **Each was byte-identical SHA256 to the freshly built `main`**. Actual pre-update server files were saved independently for rollback.
- No `index.html`, converter JavaScript, CSS, WASM, ONNX model, PHP, API, Local Worker, or existing binary was overwritten. No recursive delete/sync and no service restart.
- FTPS binary uploaded the six images/SVGs **first** and the HTML page **last**.
- Downloaded all seven files from the **real public HTTPS URL** after upload: **7/7 HTTP 200 and exact original SHA256 byte matches**. Reported MIME `text/html`, `image/svg+xml`, and `image/png` correctly.
- Launched actual Chrome on the **live HTTPS origin**, and captured both desktop and mobile screenshots with **ExitCode 0**, verifying page and image rendering.
- **After deployment**, independently re-downloaded all five existing converter/runtime assets; **5/5 SHA256 still unchanged**, proving default product safety.
- Executed focused merged-main research full SVG and BrowserFallback test suites in independent checkout: **25 passed, 9 parameterized subtests passed**. Prior research branch suite: 145 passed, 54 subtests passed.

## Canonical preservation, evidence and rollback

- Canonical source: GitHub `main`, `web/static/sa1041-preview.html` and this handoff.
- Source reports: `docs/zerobase/SA10_41_FULL_CHARACTER_BROWSER_VALIDATION_20261008.md` and `docs/zerobase/evidence/sa1041_*.json`.
- Source vector binaries and original source-authoritative visual comparisons: [SA10.41 Drive](https://drive.google.com/drive/folders/1-S22L7dMzs7tH32aLMel5bTSSsTQY7Oi).
- Public release archive under `chatGPT及びCodex用/Minimalizer/SA1041_PublicPreviewDeployment_20261008`: pre-deploy manifest and byte copies of all seven assets, public HTTPS hash verification JSON, desktop/mobile live screenshots, complete release verdict, **five SHA-checked existing runtime backups**.
- Rollback (if requested): delete **only** the seven newly deployed research preview files (HTML + 6 vector/image files). Original Minimalizer site/runtime was never modified, so do not reset/redeploy the regular converter or its assets.

## What is *not* ready for activation

The full SVG prototype still has 3,919/2,681 real Chrome wrong pixels and wrong face/arms boundaries, and original/combined polygon vertex budget violations. The browser preview is a transparent way for the owner to review the *actual experimental output*, not a claim the project passed release quality gates. The default upload conversion path remains BrowserFallback. If user wants SA10.41 to process arbitrary uploads in production, it needs explicit opt-in integration and an independently verified browser/worker pipeline; it cannot be obtained by merging this Python-only research PR.

**Outcome:** Requested merge completed and real publicly accessible SA10.41 preview deployed and verified. No default conversion behavior changed.
