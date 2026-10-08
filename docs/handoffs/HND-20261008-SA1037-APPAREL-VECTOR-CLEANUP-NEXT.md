# HND-20261008 SA10.37 → next: browser-faithful low-vertex internal SVG

## Official state

- Repository: `watarionn/Minimalizer`.
- Branch: `research/sa1032-svg-contour-proposals`, **draft PR #223 / NO MERGE / NO PRODUCTION DEPLOY**.
- Previous phases: SA10.34 original silhouette/topology corrected as research candidate but outer vertex budget FAIL; SA10.35 source-color internal planes PASS research; SA10.36 GC001 giant gray trapezoid replaced by navy/white/green geometric materials PASS research.
- Latest SA10.37 report: `docs/zerobase/SA10_37_APPAREL_VECTOR_CLEANUP_BROWSER_GATE_20261008.md`.

## What SA10.37 actually completed

- Diagnosed signed SA10.36 right navy polygon as **self-intersecting**. It is not enough to match OpenCV fill pixels; such a path is unsafe to publish as SVG.
- New strictly existing-vertex deletion algorithm in `minimalizer_zerobase/reviewed_sa10/apparel_vertex_simplifier.py` prioritizes eliminating self crossings, then deletes only vertices that pass all source color, material class, narrow necktie and face/arm constraints. Does not modify outer silhouettes, semantic owner, source color, primitive count, or add filled polygons.
- **GC001: apparel 5 polygons / 36 → 27 vertices (25% reduction); self intersections 1 → 0; lower-body Lab MSE 4606.609019 → 4533.667405 (1.5834% improvement).**
- **Raden: zero changes / hash-identical negative control**. Both real inputs have different source SHA256. Repeated outputs (metrics, polygon JSON, PNG and comparison) all 4/4 identical SHA256 per source.
- Combined targeted regression **97 tests PASS (+7 parameterized subtests)**. New code and tests in CI `.github/workflows/sa1032-svg-research.yml`.
- Implemented a source-polygon-only **real Chrome headless** SVG/clip benchmark in `tools/run_sa1037_browser_svg_probe.py`, with no raster image embedding.
- Browser result is **FAIL**: crispEdges 0px=568 different pixels; crispEdges +0.25px=558; crispEdges +0.5px=**528** best; geometricPrecision 0px=1123, +0.5px=974. There is **1 degenerate 1/2-point parent ring** which conventional browser SVG fills cannot represent. These numbers compare the isolated material SVG layer against OpenCV at 340×340, *not the entire figure*.
- Browser screenshot, HTML/SVG, reference, heatmap, all calibration results and GC001/Raden comparisons saved in Google Drive: `chatGPT及びCodex用/Minimalizer/SA1037_Apparel_Vector_20261008/`
  https://drive.google.com/drive/folders/14WDUcyt6METuUleHYZvsMPgU-LZM9tJY
- Actual metrics are in `docs/zerobase/evidence/sa1037_*.json`.

## Exact engineering files

- `minimalizer_zerobase/reviewed_sa10/apparel_vertex_simplifier.py`
- `tools/run_sa1037_apparel_simplified.py`
- `tools/run_sa1037_crosscase.py`
- `tools/run_sa1037_browser_svg_probe.py`
- `tests/zerobase/test_sa1037_apparel_vertex_simplifier.py`
- `tests/zerobase/test_sa1037_apparel_crosscase.py`
- `tests/zerobase/test_sa1037_svg_browser_probe.py`
- `docs/zerobase/SA10_37_APPAREL_VECTOR_CLEANUP_BROWSER_GATE_20261008.md`

## Next-phase acceptance requirements

1. **Browser SVG clipPath semantics**: image-preserving parent contour paths with odd-even holes; properly represent source singleton components without PNG/image overlay, introducing uncounted hidden geometry, or lowering original topology constraints. Investigate why 528 pixels differ (edge inclusion vs actual clipping parity), validate actual Chrome at the correct pixel scale and document separately anti-alias from topology divergence.
2. **Combined geometry budget**: the five new garment panels are still five distinct geometric subpaths/27 vertices, in addition to the 11 outer primitive rings (currently GC001 3604 >1887, Raden 2370 >1412) and Phase9 internal color subpaths. Do not hide geometry by calling all pieces one primitive.
3. **Quality of the full inner painting**: preserve large white shirt sections, dark navy uniform, thin central green tie; never draw eyes, mouth, nose, recolor arms, or widen tie. User should review the side-by-side at full size before promotion.
4. Require source provenance SHA verification, full-source raw topology on at least 2 real sources, part/arm continuity, SVG browser render parity, original geometric budgets, extended regression and user visual approval before any merge/production deployment.

## Operational caveat

Use GitHub as source of truth; Google Drive for original and generated binary images only under `chatGPT及びCodex用`. Avoid RDC unless actual source images or local Chrome/GPU are needed. Do not touch user's local main working tree; isolated `C:\Work\Temp\sa1033-checkout` can be refreshed by fetching only the research branch.
