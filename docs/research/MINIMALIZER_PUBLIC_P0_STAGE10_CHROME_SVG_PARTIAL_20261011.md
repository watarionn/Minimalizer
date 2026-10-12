# MinimalizerPublic StructuralRecovery P0 Stage10 — isolated Chrome SVG clip proof (2026-10-11)

**LIMITED SVG SUBSET PASS / full SVG and native secure-origin browser import NOT VERIFIED.** Chrome 144.0.7559.96 (real isolated Chromium) rendered SVG `<rect>` source-contained primitives, each with corresponding `<clipPath>` and exact original-source RGB medoid; no `<image>` and no private original-source bitmap. Pixel-exact rectangular raster reference compared to real Chromium-rendered transparent SVG at deviceScaleFactor 1 and 2:

- GC001: 8 primitives, 32 counted vertices; 340 and 680 output both 0 mismatched pixels.
- Raden: 23 primitives, 92 counted vertices; 340 and 680 output both 0 mismatched pixels.

The first attempt to serve JS modules over loopback HTTP failed `net::ERR_BLOCKED_BY_ADMINISTRATOR`. A second attempt to load SVG from Blob into `createImageBitmap` also failed to decode; **do not claim either path passes**. The successful fallback places inline SVG into an `about:blank` Chromium DOM and screenshots the actual SVG at both DPR values. This validates only the conservative geometry subset, not full-scene SVG layered blending, Chrome native secure-origin WebCrypto, normal module routing, deployed MinimalizerPublic, resvg, iPhone Safari, or licensing.

No production host or user local PC touched. Screenshot images and reproducible script remain private Drive. All these unresolved gates stay blocking.
