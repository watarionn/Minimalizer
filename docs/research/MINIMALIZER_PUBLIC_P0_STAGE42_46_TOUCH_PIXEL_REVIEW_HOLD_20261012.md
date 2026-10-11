# MinimalizerPublic StructuralRecovery P0, Stages 42–46 (2026-10-12)

Scope: **Public research branch only**, Draft PR #390. Do not touch Local Minimalizer, main, production routing, actual output renderer, or deploy. Original-only image evidence; no gen-fill, img2img, extra parts, new colors or non-source silhouettes.

## Stage42: source pixel viewport

New pure module `web/static/public-review-viewport-p0.mjs`: 1×–8× zoom with anchored coordinates, safe clamped panning, source tile auto focus, shared CSS canvas transform for underlying original, draft overlay and review boundary. Preserves the original 340×340 pixel coordinate grid; does not resample source data for processing or create semantic masks. Zoom/out/pan mode is separate from manual classification mode.

## Stage43: source-bound untrusted per-case edit memory

New pure module `web/static/public-review-session-p0.mjs`: GC001/Raden drafts are copied per case with original PNG/RGBA provenance, validates each label and historic signed eligible mask at save AND restore, rejects hidden-outside-owner pixels, forged flags and stale source SHA, keeps bounded per-case Undo. Never claims reviewers are verified. Case switching no longer destroys the other case's unsaved in-memory notes. Notes do not persist after browser reload unless manually exported; do not suggest durable autosave.

## Stage44: read-only original RGB source probe

New pure module `web/static/public-review-source-pixel-probe-p0.mjs`: verifies SHA of original RGBA, Stage04 historic owner masks, face/background exclusions via Stage31 existing guard; only returns the exact original source RGB, alpha and adjacency observations. `historicalCandidate` is mask provenance, **not sleeve/skin/hair truth**. Two real 340×340 private cases original PNG decoded to RGBA, existing source SHA replayed exactly:

- GC001 RGBA SHA `e5726add97ea1d4745d10acabe83f93195b7f991fa99d7857b5140654aa62b06`; 9,160 source-eligible signed owner pixels.
- Raden RGBA SHA `abbedd28df86789cc100824d1507434b9319e9a1407f95edf2ef5afe4c64e5d5`; 20,177 source-eligible signed owner pixels.

Original pixels, masks and probe inspection coordinates are PRIVATE only, never GitHub. Neither test case provides independently attested anatomy. Source-only mask owner still includes possible hair/background, no auto promotion.

## Stage45: private offline Chrome touch review

Private offline single-file HTML derived from Stage40: `MINIMALIZER_PUBLIC_P0_STAGE45_PRIVATE_TOUCH_REVIEW.html`, bundles original source PNGs and masks, MUST NOT be published to GitHub. Added responsive mobile-size tap controls, zoom buttons, fit source/selected tile, pan mode by default, exact pixel color readout, separate paint mode, pan without label change, two-contact pinch zoom that cancels the accidental current draft stroke, per-case in-memory draft recovery. Uses original image only.

Actual desktop Chromium and Chromium iPhone 13 **emulation**, `page.set_content`, verified source alignment, zoom controls, pan no paint, 17 synthetic test pixels in paint mode, case switch restore, 0 JS page errors. Independent iPhone Chrome? **No**. Native iPhone Safari **NOT VERIFIED**, real HTTPS secure-origin WebCrypto **NOT VERIFIED**; sandbox does not assert those. `Input.synthesizePinchGesture` on emulated iPhone produced zoom 1×→2.48× and zero label changes. These are browser interaction smoke tests, not source semantic acceptance.

## Tests and release veto

24 Stage42–43 unit tests and 10 Stage44 unit tests (34 total) pass in local Node 22. Stage46 must add both tests to research CI and verify entire Actions suite. Stage17–41 inherited Golden release veto remains. Current semantic independently attested pixels: **GC001 0, Raden 0**. Stage18 repaint, production commit, merge, deployment still **HOLD**. Stage8 SVG budget, 340/680 full-character Golden, real Public, iPhone Safari, licensing and rollback remain to check. Synthetic brush labels are neither human review nor independent identity.
