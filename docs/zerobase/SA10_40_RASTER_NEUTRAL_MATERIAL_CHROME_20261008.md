# SA10.40: Source-raster-neutral Chrome apparel edges (research NO-GO)

2026-10-08 · Draft PR #223 · NOT MERGED / NOT DEPLOYED.

## Verified result
- GC001 isolated apparel SVG: actual Chrome vs signed OpenCV reference **45 → 41 mismatched RGB pixels**, strong errors **34 → 30**.
- Residuals: 35 paint/blank and 6 color-boundary pixels; material-only edge mismatches **31 → 27**.
- Scanned **60 CSS/stroke/shift experiments**: zero safe improvements. Separately evaluated **32 actual Chrome trials** nudging existing dark/white polygon vertices by ±0.5px.
- One eligible right navy panel: material 1, vertex 1 at signed source (207,276), browser-only y adjustment **+0.5px**. **Five color polygons, 27 vertices**, source palettes, original stage37 file and full source-owner polygon unchanged.
- Independent **unclipped CV2 raster mask 0 changed pixels**. Authoritative source-render PNG SHA unchanged. Browser changed 8 pixels: 6 corrected, 2 newly different. All pixels **outside the original source owner byte-identical** to SA10.39 (3 old off-owner pixels remain). Green tie display unchanged.
- Two independently attested Chrome runs **7/7 SHA-equal core files**; independent owner audits **2/2 SHA-equal**. GC001 and Raden have different original SHA; unrelated Raden remains unchanged.
- Two-source research gate **PASS**; local extended regression **134 passed, 45 subtests passed**. Research Actions must be checked independently.

## Files
- Research source: `minimalizer_zerobase/reviewed_sa10/browser_material_edge_calibration.py`.
- Real Chrome search/replay and cross-case gate: `tools/run_sa1040_targeted_vertex_browser_probe.py`, `tools/run_sa1040_signed_render_candidate.py`, `tools/run_sa1040_two_source_material_gate.py`.
- Safety tests: `tests/zerobase/test_sa1040_*.py`.
- Seven provenance/measurement JSONs: `docs/zerobase/evidence/sa1040_*.json`.
- Original images, actual SVG and Chrome screenshot, 6-way comparison, 60+32 trial logs, audit, Raden control and SHA manifest: [Drive SA10.40](https://drive.google.com/drive/folders/15RdCMWds4V5MHrWiWcXfagIZnq_jzOKT).
- [6-way source / 528 / 69 / 45 / 41 / OpenCV comparison](https://drive.google.com/file/d/1pnx4U6p4-p2YEiMZ_fx74JC0Ns1b3uVt/view).

## Unresolved non-negotiable release gates
1. **Browser exact SVG parity FAIL: 41 nonmatching pixels, 3 off-owner.** Small browser-only calibration is opt-in research, not universal source geometry.
2. Original full outer vector budget FAIL: GC001 **3,604 >1,887**, Raden **2,370 >1,412** before extra internal color paths and SVG mask strokes.
3. Chrome test covers only isolated clothing, NOT whole character, face/arms or z-order. No second independent *positive* matching outfit case. Human visual approval pending.

**Decision:** SA10.40 research result complete; production **NO-GO**. Keep #223 draft and unmerged. Next phase should prioritize whole-character Chrome SVG parity, honest combined vertex budget and additional independent positive images.
