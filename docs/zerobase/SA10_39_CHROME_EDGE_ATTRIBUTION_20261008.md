# SA10.39: Chrome SVG residual edge audit and counted source-contour stroke

Date: 2026-10-08 · Repository `watarionn/Minimalizer`, research branch `research/sa1032-svg-contour-proposals`, draft PR #223.

## Result

**SA10.39 research evidence and diagnostic phase complete. Production NO-GO.** A previously frozen silhouette is maintained and the apparel colors and polygons are not modified.

GC001 isolated material-layer SVG had **69 Chrome/OpenCV mismatched RGB pixels** in SA10.38. Adding an explicitly counted **1.15px same-white source parent-contour outline stroke** reduced this to **56 pixels** on actual attested headless Chrome, a **18.8406% reduction** from SA10.38 and **89.3939% reduction** from SA10.37's 528 pixels. Strong mismatches (max RGB channel error >48) fell from 51 to 45.

The stroke **reuses the existing source boundary points**, not new source pixels. It is a new **paint pass** that explicitly repeats **152 parent contour point occurrences** in the geometry complexity accounting; not a free correction or excuse to meet the total vertex budget. The five source-backed apparel subpaths still have **27 vertices**. Existing owner, original Phase8 outer contour and original source SHA remain identical. A raster-neutral one-point source hole can be omitted only after independently proving zero canonical owner-pixel changes.

## Residual geometry attribution

The signed SA10.39 verifier `tools/run_sa1039_svg_residual_audit.py` reconstructed the authoritative OpenCV pixels directly from the independently hashed source outer geometry and five original material polygons, then checked the real browser execution SHA logs.

- Chrome/OpenCV different pixels: **56** across **37 connected mismatch regions**.
- Painted-versus-unpainted occupancy: **50 pixels**.
- Different RGB in pixels both renderers painted: **6 pixels**.
- Within source owner AND material outline (1px-expanded boundary): **25 pixels**.
- Material outline only: **31 pixels**.
- Source-owner outline only: **0 pixels**.
- Outside both owner and material outlines at 1px-expanded distance: **0 pixels**.
- The 15-pixel horizontal band at y=245 in SA10.38 is eliminated by the additional source-boundary stroke.

This attributes all remaining errors to existing geometry raster semantics rather than unexpected new structures. The **SVG exact browser gate remains FAIL**, not PASS.

## Parameter sweeps and rejected alternatives

Independent real Chrome experimental runs compared source-contour strokes 0.5–2.0px, original path without stroke, alternative dark strokes and line-join choices. 1.15px yielded **56 pixels**, while 1.25–1.35px gave the same pixel count with larger RGB error. 1.5px gave 57 pixels.

A second sweep assessed four parent outline widths × three material outline widths × three hole outline widths (36 combinations). **Best was still 56 pixels**, with the old material stroke=1.0px and hole stroke=1.0px. Per-panel independent outline sweeps on the five apparel regions each failed to improve on 56; those edits increased mismatches to at least 58.

Do not apply the 1.15px calibration generically. It was fit to GC001 on a 340×340 isolated material panel, not all character assets and resolutions. No additional matching outfit was validated. The independent Raden input is deliberately a **no-op** because no corresponding five-panel uniform was observed.

## Code and quality checks

- `tools/run_sa1038_vector_mask_browser.py`: added opt-in `--parent-outline-stroke` (default 0), bounded [0,2], correctly accounting for additional parent source-ring drawing.
- `tools/run_sa1039_svg_residual_audit.py`: independently SHA-verifies saved browser and vector artifacts, reconstructs OpenCV material reference, classifies all mismatches against parent and material boundaries, rejects evidence drift.
- `tools/run_sa1039_edge_research_gate.py`: tests prior (69px) vs current (56px) genuine browser evidence, independent residual audit and SHA-distinct unchanged Raden control. **Research gate PASS**, **release NO-GO**.
- `tests/zerobase/test_sa1039_svg_residual_audit.py`, `test_sa1039_edge_research_gate.py`, updated `test_sa1038_vector_mask_browser.py`: enforce explicit SVG stroke accounting, accurate pixel attribution, no fake browser data and no weakened quality gates.
- Focused local targeted suite: **16 passed, 7 subtests passed**. Full branch CI contains SA10.39 tests. Latest run should be verified at the research branch tip before any claim of CI success.

Measured machine-readable GitHub evidence:
- `docs/zerobase/evidence/sa1039_gc001_chrome_outline_20261008.json`
- `docs/zerobase/evidence/sa1039_gc001_residual_attribution_20261008.json`
- `docs/zerobase/evidence/sa1039_two_source_edge_gate_20261008.json`

Verified Drive files: [`chatGPT及びCodex用/Minimalizer/SA1039_ChromeEdge_20261008`](https://drive.google.com/drive/folders/19Zj4LGJZhVeePFIj4KSJ3jLnbnGGF5js), 14 source-SHA-matching files plus a manifest, containing actual Chrome PNG, expected OpenCV PNG, SVG/HTML, differential images, raster attribution, calibration sweeps, Raden no-op metrics and source logs.

## HARD HOLD, not waived

1. **SVG exact parity is FAIL (56 pixels remain).**
2. Original Phase8 **outer vertex budget fails**: GC001 **3,604 >1,887**, Raden **2,370 >1,412**. Additional apparel polygons, internal color planes, hole-outline strokes and the new 152-point parent-outline paint pass are counted, not hidden.
3. Only an **isolated apparel layer** was rendered in Chrome; full-character z-order and cross-owner safety in an actual browser are not yet validated.
4. The stroke width is a GC001-specific research calibration, not proven transferable. A second independently matching outfit is missing.
5. Human art review is pending. **PR #223 must remain draft and unmerged, no production deploy.**

**SA10.40 suggested next:** investigate more exact raster-edge representation without increasing traced geometry or embedding pixels. Prioritize decreasing total contour complexity while honoring real source silhouette, visible arms, and topology; run browser parity on an independent matching outfit and then a full composited scene.
