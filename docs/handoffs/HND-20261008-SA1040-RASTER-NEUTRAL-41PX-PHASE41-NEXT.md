# HND-20261008 SA10.40 → SA10.41

**Canonical repository:** `watarionn/Minimalizer`, branch `research/sa1032-svg-contour-proposals`, PR #223 **DRAFT / UNMERGED / UNDEPLOYED**.

Full completion record: `docs/zerobase/SA10_40_RASTER_NEUTRAL_MATERIAL_CHROME_20261008.md`.

## Completed
- User likes source silhouette; gray clothing trapezoid was fixed with **5 polygons and 27 total signed apparel vertices**, navy/white/green, no eyes/mouth, protect arms/tie.
- Earlier isolated apparel SVG real-Chrome differing pixels: SA10.37 **528**, SA10.38 **69**, SA10.39 **45**, now SA10.40 **41**.
- No safe win among 60 per-polygon browser CSS settings. A ranked source-vertex trial over 32 actual Chrome screenshots found **right dark uniform panel #1 / vertex #1 / y +0.5px**.
- This is a **browser-render-only** 0.5px vertex adjustment. Signed Stage37 source authority untouched; **canonical unclipped CV2 polygon raster 0 pixel change**, same source reference PNG SHA, same material colors and geometry count.
- Chrome 45→41: **6 corrected + 2 newly mismatched**, **8 actually changed**. Original outside-owner browser RGB absolutely byte-identical (still **3** existing off-owner pixels), green tie pixel mask unchanged. Residual 35 blank/paint + 6 wrong-color; material-only boundary mismatch 31→27.
- **Two independently executed Chrome source/HTML/SVG/screenshot attestation runs 7/7 SHA-equal files** and independent owner audit **2/2 SHA-equal**. Original GC001 and Raden SHA distinct; Raden negative control never acquires a shirt or tie.
- Two-source research gate **PASS**, expanded local tests **134 PASS +45 subtests**; code compiled. Final research Actions workflow should be checked.
- All 24 data/source/visual artifacts plus SHA manifest verified under [Drive SA10.40](https://drive.google.com/drive/folders/15RdCMWds4V5MHrWiWcXfagIZnq_jzOKT). Main user-facing [6-way comparison](https://drive.google.com/file/d/1pnx4U6p4-p2YEiMZ_fx74JC0Ns1b3uVt/view).

## Code/evidence index
- `minimalizer_zerobase/reviewed_sa10/browser_material_edge_calibration.py` has guarded opt-in SVG style and raster-neutral vertex adjustment.
- `tools/run_sa1040_targeted_vertex_browser_probe.py`, `run_sa1040_signed_render_candidate.py`, `run_sa1040_two_source_material_gate.py`.
- `tests/zerobase/test_sa1040_browser_material_edge_calibration.py`, `test_sa1040_source_raster_neutral_vertex.py`, `test_sa1040_two_source_material_gate.py`.
- Seven JSON evidence records: `docs/zerobase/evidence/sa1040_*.json`.
- `.github/workflows/sa1032-svg-research.yml` includes the tests and compiles tools.

## Stage 41 priorities and protection
1. **Full-character Chrome SVG replay** instead of spending more iterations on isolated clothes. Verify z-order, face/arm immutable regions, outer silhouette and five original material subpaths, without embedding pixels or drawing facial features.
2. Independently reduce **total original source contour vertex budgets**: GC001 3,604 vs 1,887 limit; Raden 2,370 vs 1,412. Include *all* apparel internal polygon points plus parent-hole strokes and any extra masks. Never hide complexity or lower source topology gates.
3. Add an independently **positive five-plane matching garment** test, not just negative Raden. Keep source class precision, narrow green tie, owner topology.
4. Exact Chrome SVG parity still **FAIL (41 different pixels; 3 off-owner)**. Improvement gate PASS is *research only*, never product.
5. Human art review pending. Do not merge PR #223 or deploy until all required release gates pass.

**Operational:** GitHub and Drive are canonical; use RDC only for the original source and actual local Chrome when needed. Keep research in separate checkout, no source/main mutations.
