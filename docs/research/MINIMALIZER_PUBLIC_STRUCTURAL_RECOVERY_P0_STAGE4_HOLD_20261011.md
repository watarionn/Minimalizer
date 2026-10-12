# MinimalizerPublic P0 Stage4 — true Chromium preview display parity (2026-10-11)

**Chromium Canvas display parity PASS; browser module import and full Product integration NOT VERIFIED / HOLD.** This is a narrow browser display check on the exact frozen Stage3 output bytes. No product route, main, Local Worker, production, source photo or signed authority modified.

- Actual isolated headless Chrome/Chromium **144.0.7559.96**, 340×340 CSS and DPR 1/2, both GC001 and Raden.
- Four in-memory `CanvasRenderingContext2D.putImageData` then `getImageData` replays; **0 mismatched channels** each; captured real browser screenshot at 340×340 and 680×680; **0 pixel/channel differences** against Node Stage3 RGBA and exact 2× nearest-neighbor expansion.
- Source RGB originals are not loaded into these Chrome pages; only the already computed private candidate preview RGBA is injected in-memory.
- An attempted localhost module import and file:// navigation both produced `ERR_BLOCKED_BY_ADMINISTRATOR` in this tool environment. We did **not** bypass those restrictions. Thus `import()` of the isolated JS source, its WebCrypto pins inside Chrome, complete production route, SVG clipping/resvg, and Apple/iPhone Safari are **not verified** and must not be represented as PASS.
- Actual signed Stage8 source-ring geometry **budget still fails**: GC001 3,604 > 1,887, Raden 2,370 > 1,412. The accepted GC001 material subpaths add more vertices, not a budget solution.
- The P0 goal is better *recognizable major structure*, not simply Canvas parity; source-lineage artifact, external Golden review, browser module parity and actual output quality are all HOLD.

Private full evidence: `PartPreservation_Stage3_20261011/MinimalizerPublic_P0_Stage3-4_PRIVATE_20261011.zip` (including signed lineage metadata, source-vs-preview comparisons, Chrome DPR1/2 screenshots, replay runners and SHA manifest). This document has no private image raster.

**Next Stage5 priorities:** recover visibly missing large parts, especially Raden bow/corset/ruffled sleeves and GC001 eyewear/collar; bind source-supported parent ownership, correct occlusion, and re-evaluate recognizability side-by-side at Golden while keeping face feature suppression. Do not merge a HOLD branch into main.
