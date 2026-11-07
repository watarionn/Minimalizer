# MinimalizerPublic P0 Stage186–190 / iPhone Private Human Review HTTPS

Date 2026-10-13 JST. Original source and annotated pixels remain PRIVATE. Current research PR #393 Draft / GOLDEN HOLD, normal Public and Local unchanged.

## Why the old HTML ZIP was replaced
iOS Files app / Quick Look can fail to execute JavaScript in offline HTML. Directly sharing original-embedded HTML does not ensure native Safari execution. Use a **source-free generic HTTPS viewer** plus a **separate private per-reviewer original RGBA file** chosen via iOS Files picker.

## Operational live viewer
https://watarionn.github.io/minimalizerpublic-iphone-reviewer/

Source-free public GitHub repository: https://github.com/watarionn/minimalizerpublic-iphone-reviewer ; deployment commit d8e291f. GitHub Pages status **built** and actual Windows remote HTTPS GET **200** for index.html, review.js, review.css. No raw original pixels, original PNG, private preview or human draft is committed on Pages or Minimalizer repo.

## Stages
- 186: independent HTTPS GitHub Pages source-free viewer, iPhone responsive CSS, no cross-origin fetch, CSP connect-src none.
- 187: Reviewer A / B individually packaged PRIVATE ZIP. Each ZIP has GC001.review-source.json and Raden.review-source.json embedded original 340×340 exact RGBA and original SHA pins, plus checksums and iPhone instructions. These are NOT put on GitHub.
- 188: touch/pointer drawing, line interpolation, 10 proposal roles, drawing vs 2-finger manual panning, 1–8x zoom slider, original-tile navigation 0..120, undo/redo, skip transparency. UI is classification only, never alters original image.
- 189: on-device SHA/role/alpha validation, Safari localStorage auto/manual save of only draft JSON, SHA+reviewer+case scoped restore, iOS navigator.share / canShare Files share sheet with JSON download fallback. No network source transmission. User must manually export JSON backups because device storage can be evicted.
- 190: no human forgery promotion, release flags false, fail cross-case SHA mismatch and invalid RLE, tests. Existing Stage181–185 private receipt audits remain applicable.

## Verification
Chromium mobile emulation viewport 390x844, dpr3, 12 functional browser checks PASS: SHA, responsive layout, pointer drawing, storage recover, undo/redo, pan/zoom, original compatible JSON, A/B isolation, source-tampering rejection, cross-case draft rejection, declared source SHA rejection and no JavaScript errors. Chromium test adapted opaque test origin's crypto/storage shims because container browser networking is blocked; this is NOT a physical iPhone Safari pass.
12 new source-free Node research CI tests added for app privacy, CSP, source pins, UI, 10 role taxonomy, storage, export, fail-close.
HTTPS 200 in actual Windows remote browser's network layer; native iPhone Safari human acceptance remains **NOT YET VERIFIED**. The user needs to follow A/B instructions on an actual iPhone and send source-free diagnostics or real reviewed JSON.

## No Golden release
Reviewer persons independently verified 0; submitted actual reviewed source semantic pixels 0. Full-body original Stage8 historic GC001 3604>1887 and Raden 2370>1412 vertex-budget FAIL. No physical Safari acceptance or actual production rollback exercise. Stage135, Stage51, normal Public, Local, main untouched. PR #393 stays Draft, GOLDEN HOLD and not for merging; the isolated Pages reviewer tool may be used as a standalone private-file client only.
