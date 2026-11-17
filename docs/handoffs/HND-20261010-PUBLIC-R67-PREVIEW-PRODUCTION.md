# MinimalizerPublic R67 read-only production preview | 2026-10-10

**SHIPPED and verified on existing Public site**, separate from the default image converter.

## Owner request and scope

The owner requested a temporary production update in order to personally inspect the current Minimalizer research. R67–R73 research changes were **specific to two signed original photos and their already-observed Stage8 source masks**, not a generic image upload processor, and did not pass semantic face/arms/garment/staff correctness, historic vertex caps or human Golden review. Therefore, only a **new, independent, opt-in production inspection page** was published. None of the existing conversion files, default profile, Local Worker, image upload API, PHP, ONNX/WASM assets or host cache configuration was overwritten.

Live URL:

**https://cf278796.cloudfree.jp/minimalizer/static/public-r67-review-20261010.html**

Regular converter remains **https://cf278796.cloudfree.jp/minimalizer/**.

This preview shows **Stage8 original 11-owner colored-mask composition ONLY**, before and after research selection. It does **not** claim to show the complete later Stage9/interior/SA10.41 garment scene, and it does **not** apply R67 to arbitrary user-uploaded photos. Original signed source photographs and private source masks have not been published.

### What is actually visible

- **GC001:** 12 altered source-owned canvas pixels (right arm 8, left arm 3, major clothing 1).
- **Raden:** 7 altered pixels (right arm 3, major clothing 4, left arm 0).
- Two images each: original owner-mask flat RGB, R67 research-only preview, plus a magenta pixel change locator. Clicking or stepping through changed pixels displays a 20-by-20 source-owner color crop, nearest-neighbor magnified to 180-by-180, so extremely small differences can be inspected.
- Responsive 390 CSS pixel / DPR3 simulated mobile screen, but **actual iPhone Safari owner sign-off is still pending**.
- The page contains no form or upload/POST/fetch workflow; all six images are already pre-rendered, so no original input photo is sent to a server.

## GitHub artifacts and actual production operations

Authoritative HTML: `web/static/public-r67-review-20261010.html`. Isolated tests: `tests/test_public_r67_preview_readonly.py` (5 new tests), together with `tests/test_minimalizer_page_split.py` = **8 PASS**. The base Public runtime files are unchanged by this PR. Earlier 258 research regressions PASS separately on R67 research Draft PR #386, which remains **unmerged** and **research-only**.

Published only seven **new** files to existing Shin Free Server saved WinSCP FTPS session, directory `/cf278796.cloudfree.jp/public_html/minimalizer/static/`:

1. `public-r67-review-20261010.html`
2. `public-r67-review-20261010/gc001-before.png`
3. `public-r67-review-20261010/gc001-after.png`
4. `public-r67-review-20261010/gc001-diff.png`
5. `public-r67-review-20261010/raden-before.png`
6. `public-r67-review-20261010/raden-after.png`
7. `public-r67-review-20261010/raden-diff.png`

All six PNGs were created from the original source-signed Stage8 **flat palette/z-order masks**, with R67 candidate mask SHA cross-checked against the private `LibraryConvergence_R67_R73_20261010` manifest. No original source photo was copied to a public output or production FTPS target. The HTML and all six new PNGs had been **HTTP 404** in the public path before deploying, so no unrelated server asset was replaced.

Before deployment, fetched/read-only backed up and SHA-256 hashed the live `/minimalizer/` HTML and six live scripts/styles/previous preview, namely `static/app.js`, `static/public-route.js`, `static/browser-fallback.js`, `static/canonical-contour.js`, `static/styles.css`, `static/sa1041-preview.html`. (Seven total.)

**Production verification:** Re-fetched all seven new files over actual production HTTPS: **7/7 HTTP 200, correct MIME, bytes and SHA-256 identical to the validated local release files.** Re-fetched all seven existing original runtime assets: **7/7 byte SHA-256 identical to their predeploy backups**. Thus the primary image converter was not changed by this release.

The live URL was opened in real Chrome. **Desktop and 390px/DPR3 mobile emulation PASS**, both subjects show exactly six natural-sized 340px PNG frames, the working interactive next-difference control switches the first subject from `1 / 12画素` to `2 / 12画素`, and the 390px mobile viewport has no horizontal overflow. Captured private actual-live desktop and mobile screenshots and all HTTP hash/manifests for archive.

## Rollback and outstanding gates

Rollback is **delete only the seven new public preview files**, then remove the newly added empty `public-r67-review-20261010/` directory. Do not change `index.html`, `app.js`, `public-route.js`, `browser-fallback.js`, `canonical-contour.js`, existing `sa1041-preview.html`, Local Worker or any other website. Verify these seven assets go 404, while existing runtime hashes remain identical to preserved predeploy baseline. Exact predeployment public runtime copies are archived for recovery but should not be reuploaded unless a distinct accidental mutation is evidenced.

Still **NO-GO** for *default* production integration of the research code: no independent human source-photo semantic owner/anatomy signoff, Stage8 original vertex cap still GC001 3604 >1887 and Raden 2370 >1412, full scene resvg/Facet DPR2, actual physical iPhone Safari Golden visual signoff, legal vendor redistribution and true default-engine/host rollback gate remain unresolved.

### Evidence and storage

Google Drive canonical archive (private): `chatGPT及びCodex用/MinimalizerPublic/PublicR67_ProductionPreview_20261010/`.

Includes release HTML and six generated public-only PNGs, original site seven byte-exact runtime backups, predeploy and postdeploy HTTPS SHA audit JSON, actual live Chrome desktop/mobile PNG screenshots, publication-image SHA manifest, and source-generator scripts. Every file needs Drive read-after-write SHA before declaring archive complete.

**Conclusion:** Temporary **standalone live inspection page SHIPPED**. Research code remains held, default upload converter unchanged. Do not describe this deployment as R67 integrated into normal arbitrary-photo browser processing.
