# MinimalizerPublic Stage 51 temporary public preview release

Date: 2026-10-12 (JST)

## What was actually released

- Public URL: https://cf278796.cloudfree.jp/minimalizer/static/structural-p0-stage51-preview.html
- GitHub `main` commit: `05eb115717265d8d4612b4de7777db6410d17270`
- Source: `web/static/structural-p0-stage51-preview.html` (a **new** stand-alone static research comparison page)
- Public file: 10,962 bytes, SHA-256 `3cdc5fbe224b9b0735d0edb6def4f55caf874fbabc70195b615a0470337d7457`.
- Added via the existing WinSCP saved FTPS session to the explicit MinimalizerPublic static directory. Uploaded a `.uploading` temporary file and renamed it to the new public HTML filename after upload. No existing file was overwritten; no recursive synchronization or delete.
- All original input images, original RGBA pixel buffers, historical masks and private annotator HTML remain PRIVATE and were **not** published.

## Scope and visual honesty

This preview *reuses already-public SA10.41* GC001/Raden full-character vector SVGs, OpenCV-geometry reference PNGs and browser-difference PNGs. It adds Stage 51's measured, qualified diagnostics (full-scene Stage8 vertex-budget violations and a distinct feature-subset DPR2 test), case toggle, SVG/difference toggle and an adjustable reference/SVG overlay. It does **not** introduce a new Stage 51 rendered output, runtime minimalization algorithm, or a generic upload+conversion route.

Normal MinimalizerPublic conversion, `public-route.js`, BrowserFallback, shared page, Local Minimalizer and the user's PC's existing dirty worktree were not changed. Research PR #390 stays **Draft/unmerged**, Golden and anatomy gates HOLD.

## Remote read-after-write checks

Actual public HTTPS read-back with no-cache query returned status **200**, MIME `text/html`, exactly 10,962 bytes and SHA-256 exactly matching both the pre-upload staging file and GitHub source. The six existing SA10.41 resources, live `index.html`, `static/public-route.js`, and `static/browser-fallback.js` all returned **HTTP 200** with expected content types. See separate machine-readable evidence JSON.

Selenium headless real Chrome on the public HTTPS URL confirmed page load, reference/SVG asset load, GC001↔Raden toggle, SVG↔difference-image toggle, and overlay opacity control. Desktop (1280×960) and mobile-width emulation (390×844) screenshots recorded on the authorized workstation under the release staging directory. Emulation is **not** real iPhone Safari proof.

## Known quality HOLD

- Entire older SA10.41 browser SVG differs from geometry reference for 3,919 pixels (GC001) and 2,681 pixels (Raden). Protected face/arm boundaries are not accepted.
- Full-scene Stage8 vertex counts GC001 3,604 > 1,887; Raden 2,370 > 1,412.
- Stage51 feature-subset 340/680 deterministic raster test verified exact source contours; epsilon=0.5 reduced contours mismatch at 680 by 148 GC001 / 428 Raden, so **not adopted**. Not a new browser pixel-perfect full-body proof.
- Zero independently verified anatomical sleeve/skin/hair owner pixels. No untrusted draft authorizes painting. iPhone Safari not tested.

## Rollback

Use the saved authorized WinSCP FTPS session; explicitly enter the Minimalizer static document root and **remove only** `structural-p0-stage51-preview.html`. No revert of main converter assets is required because they were not modified. The GitHub main addition can be reverted separately if the temporary preview is retired. Do not delete the six existing SA10.41 resources.

## References

- Research: https://github.com/watarionn/Minimalizer/pull/390
- Existing SA10.41 preview: https://cf278796.cloudfree.jp/minimalizer/static/sa1041-preview.html
- Regular MinimalizerPublic: https://cf278796.cloudfree.jp/minimalizer/
