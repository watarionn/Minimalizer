# SA10.38: Chrome-faithful SVG material mask research (69px remaining; NO-GO)

Date: 2026-10-08 JST · `watarionn/Minimalizer` · research branch `research/sa1032-svg-contour-proposals` · **DRAFT PR #223**.

## Decision

**SA10.38 research prototype, genuine Chrome verification, negative control, automated tests, evidence preservation: COMPLETE.**

**SVG exact-pixel parity gate: FAIL. Full geometric budget: FAIL. Production promotion: NO-GO.**

The user wants the approved outer silhouette preserved, apparel defined by a few crisp geometric color planes, and no loss of arm/color/topological provenance. SA10.37 had fixed a huge gray trapezoid and reduced five source-observed uniform / white shirt / green necktie polygons from 36 to **27 vertices** without self intersections. However an isolated browser SVG clipPath and OpenCV vector reference disagreed in **528 pixels** at best.

### Breakthrough: source contour-specific SVG raster behavior

Measured the original signed GC001 OpenCV fill vs an actual **Chrome headless** screenshot, not simulated web rendering.

1. Distinguish **color-plane raster semantics** from **source-owner clipping**. With standard crisp SVG polygons, no clipping already leaves 435 mismatch pixels. Giving each existing apparel polygon a **1px stroke in its already-observed fill color** and placing vertices at pixel-center shift +0.5px leaves **35 mismatches without parent clipping**. This is the central OpenCV-inclusive boundary vs SVG center-of-pixel difference.
2. Ordinary SVG parent `clipPath` still disagrees at many contour-hole boundaries. Use a **source-vector-only luminance SVG `mask`** instead, with the verified existing owner contour's `fill-rule="evenodd"` and **5 explicitly counted source hole-boundary stroke passes** (same actual source points, no new source parts).
3. Calibrate the source-owner mask path separately at (-0.25px,+0.5px), retaining the apparel material +0.5px center shift and 1px same-color strokes. The mask's hole-edge passes also use 1px strokes. The offsets are **GC001 calibration experiments only, NOT production defaults**.
4. Verify an unusual 1-point **hole contour** is raster-neutral: the canonical source-owner `rasterize_primitive_candidate` was run before/after omitting this non-SVG-valid ring and had **exactly 0 changed pixels**. Omission is allowed ONLY by this per-scene proof. A one-point filled island that would change raster pixels is rejected.
5. Neither the SVG nor screenshot embeds/paints a PNG, bitmap, base64 source pixel array, or generative image. Only existing source-bound parent contour and 5 existing clothing polygons are rendered. New mask stroke drawing paths are **counted**, not hidden.

### Verified real browser result (isolated apparel layer, 340×340 pixels)

| Measurement | SA10.37 clipPath | SA10.38 vector mask |
|---|---:|---:|
| Chrome RGB mismatch vs OpenCV | **528** | **69** |
| Reduction in mismatched pixels | baseline | **86.9318%** |
| Strong mismatches, max channel delta >48 | 388 | **51** |
| Mean absolute RGB channel error | 0.536459 | **0.080363** |
| Parent micro-rings without browser-valid fill path | 1 unverified | **1 omitted with canonical 0-pixel parity proof** |
| Source-derived hole boundary stroke paint passes | 0 | **5, 31 repeated contour vertices explicitly counted** |
| New material polygon subpaths | 5 | 5 (27 material vertices) |
| Real browser executed, source HTML/SVG/screenshot verified | Yes, standalone | **Yes, binary and input/output SHA256 attested** |
| Exact SVG parity gate | **FAIL** | **FAIL (69 pixels remain)** |

SA10.38 residual pixel audit:
- **63** mismatches in painted vs unpainted occupancy.
- **6** RGB mismatches inside pixels that both renderers paint.
- **54** near a reference RGB boundary (3×3 dilated Canny zone), **15** farther away.
- **51** contain an RGB channel difference above 48.

This indicates mostly subtle **raster edge coverage / source owner clip inclusion**, not a large reappearance of the gray clothing trapezoid. It does **not** establish full-scene vector parity or subjective beauty, so the hard gate cannot be waived.

The additional stroke geometry is not free: the SVG contains a source-owner fill path (7 nondegenerate rings, 152 vertices), **5 extra hole-edge stroke paths using 31 point occurrences**, and 5 already-source-signed clothing polygons (27 vertices), in addition to the external scene's other original primitives/Phase9 internal planes. The source polygon includes one 1-point hole that is omitted *only* after canonical raster-neutral verification.

### Chrome provenance and reproducibility

- `tools/run_sa1038_vector_mask_browser.py` first validates **SA10.34 existing outer scene SHA, SA10.37 candidate scene SHA, original source SHA, the previous Phase04/Phase36 owner and color evidence, five non-self-intersecting polygons, colors, owners, and unchanged face/arms**.
- It generates a true, static SVG/HTML, an independent **OpenCV reference**, and a signed research metrics JSON. The second command executes a real installed **headless Chrome binary** in a fresh isolated profile (no user Chrome session) at 800×600 with device pixel ratio 1 and captures the top-left 340×340 SVG canvas.
- Both executable SHA256 and SVG/HTML/screenshot SHA256 are recorded in `real_chrome_execution.json`. The Windows-packaged Chrome `--version` console command may hang; its optional timeout is logged, not mistaken for missing browser rendering.
- **Two independent GC001 real-browser executions:** SVG, HTML, OpenCV expected PNG, Chrome screenshot PNG, full metrics and difference PNG **6/6 SHA256 identical**.
- **Juufuutei-Raden negative control:** its source SHA is distinct, apparel grammar doesn't match, previous SA10.37 candidate is byte-for-byte unchanged. No costume-specific green tie is invented. Raden is *not* claimed to have an equivalent Chrome apparel-rendering benchmark, because no corresponding five-panel uniform was generated.
- The source-distinct cross-case **research improvement gate PASS** requires Chrome execution evidence, 80% or more mismatch reduction, raster-neutral source singleton proof, counted additional SVG passes, existing primitive preservation and Raden's unchanged image. It explicitly records **SVG exact parity FAIL** and never authorizes release.

### Tests, source and artifacts

New verified code:
- `tools/run_sa1038_vector_mask_browser.py`: owner source contour validation, exact micro-hole raster neutrality, explicit all-vector mask and material outline SVG generation, actual standalone Chrome execution with SHA attestations, pixel audit and hard fail.
- `tools/run_sa1038_two_source_browser_gate.py`: two independent source SHA / no-op / strictly fail-closed research coverage.
- `tests/zerobase/test_sa1038_vector_mask_browser.py`: 6 tests for positive/negative source ring neutrality, SVG-only geometry, tampered SHA protection, fabricated screenshot cannot pass, and pixel mismatch hard failure.
- `tests/zerobase/test_sa1038_two_source_browser_gate.py`: 5 tests for source-distinct coverage, fabricated browser artifacts, 80% threshold, unrelated character immutability, and release gates.
- `.github/workflows/sa1032-svg-research.yml`: added tests and tool compilation.

Full focused local regression: **108 tests PASS, 11 parameterized subtests PASS** (same unchanged original quality thresholds). Independent research GitHub Actions branch-head status must be checked before calling CI successful.

Machine-readable evidence in this PR:
- [GC001 real Chrome pixel evidence](evidence/sa1038_gc001_attested_chrome_vector_mask_20261008.json)
- [Real headless Chrome executable/inputs/screenshot hash attestation](evidence/sa1038_gc001_real_chrome_execution_20261008.json)
- [Two-source improvement research and untouched control](evidence/sa1038_gc001_raden_two_source_browser_20261008.json)

All Chrome screenshots, official expected material layer PNG, pixel heatmap, rendered HTML/SVG, tunable stroke/offset sweep results, source-control scene evidence and independent SHA manifest stored at:

[Google Drive `chatGPT及びCodex用/Minimalizer/SA1038_VectorMaskChrome_20261008/`](https://drive.google.com/drive/folders/1rpCp_Ypg26XEdxL1L55ktQulySXFHkJs)

The main comparison file is `GC001_browser/chrome_vector_parity_before_after_comparison.png`, displaying **SA10.37 actual Chrome (528)** / **SA10.38 Chrome (69)** / **official OpenCV expected** / **difference heatmap**. Fourteen named artifacts plus `manifest.json` were saved and each mounted Drive copy was checked against its input SHA256.

### Open release blockers (not relaxed)

1. **Actual browser exact raster parity: FAIL, 69 pixels.** A small MAE or 87% improvement is insufficient to call the original SVG hard gate PASS. The source-owner mask calibration may be overfit to GC001 and must be validated independently against other matching apparel cases.
2. **Outer/total geometry vertex budget remains FAIL.** Original Phase8: GC001 3,604 vs original 1,887 ring vertices, Raden 2,370 vs 1,412. Five 27-vertex clothing shapes, previous Phase9 color planes, the mask's 5 hole-stroke paths and their point occurrences must all be counted. No extra paths may be hidden from complexity scoring.
3. **Only an isolated material-layer SVG was Chrome-rendered.** Full-character z-order, face/arm protection and cross-owner clip interactions still need a complete-browser SVG reference. The original rigid 11 owner count remains unchanged; SVG adds color and hole-edge drawing passes.
4. **Human visual approval PENDING**, and generic garment materials beyond a navy/white/green uniform still not validated.
5. **No production or merge.** PR #223 remains draft; source input, production worker and live BrowserFallback unchanged.

**Engineering next:** isolate the remaining 63 coverage mismatches using source owner/contour adjacency maps, repair the actual SVG rasterization model or prove a browser-valid parity-preserving geometry representation. Then test a second matching outfit without GC001-specific offsets, tackle the inherited full polygon vertex budget, and only then request visual signoff/promotion.
