# SA10.39: SVG source-silhouette-safe top-edge repair, actual Chrome 45px HOLD

Date: 2026-10-08 JST · Repository: `watarionn/Minimalizer`
Branch: `research/sa1032-svg-contour-proposals` · PR #223 **draft, unmerged**.

## Decision

**SA10.39 signed SVG boundary research, two real-image control verification, and deterministic evidence preservation: COMPLETE.**

**Production release: NO-GO.** This is an isolated apparel-layer Chrome rasterization experiment, not the full Minimalizer/browser rendering pipeline. Exact browser SVG parity and original total vector budget still FAIL. User has approved the **outer silhouette direction**, not the result of relaxing source ownership or drawing more detail.

## Root-cause diagnosis

The independently attested SA10.38 candidate with the existing 5 apparel color polygons (2 dark uniform / 2 white shirt / 1 thin green tie, **27 vertices**) had **69 mismatched RGB pixels** against the authoritative, source-owned OpenCV renderer. Of these 69:
- **63** were paint occupancy / blank disagreements; **6** were conflicting RGB where both were painted.
- **23** were on the single garment top row (y=245), notably green and white panels at the source owner boundary.
- The actual source `lower_body` owner has **two horizontal top edges already recorded in the same signed source polygon rings**:
  - ring 1: (91,245) → (230,245)
  - ring 0: (233,245) → (238,245)
- Canonical owner-mask rasterization at y=245 produces **exactly** x=91..230 and x=233..238, with no pixels at y<245. These original contour endpoints were never invented from a source bitmap.
- The material SVG and parent luminance mask rasterizers include boundaries differently than OpenCV, especially at pixel centers.

### Failed optimization detected and rejected

Adding a thick white stroke to the **entire** original parent contour reduced the overall Chrome discrepancy to **56** but introduced a **source silhouette regression**:

| Metric | SA10.38 baseline | Broad-outline 56px (REJECTED) | SA10.39 selective top-edge |
|---|---:|---:|---:|
| Isolated apparel Chrome RGB mismatches | 69 | 56 | **45** |
| Strong RGB mismatches (channel >48) | 51 | 45 | **34** |
| Differences OUTSIDE original signed owner | **3** | **22** | **3** |
| In-owner mismatches | 66 | 34 | **42** |
| Top owner boundary row (y=245) mismatches | 23 | 0 | **0** |
| Wrong colors on pixels painted by both renderers | 6 | 6 | **6** |
| Paint-vs-blank disagreements | 63 | 50 | **39** |
| Source geometry/owner/material count | unchanged | unchanged | unchanged |

**The 56px version is NOT an acceptable improvement.** It adds 19 off-owner painted pixels, violating the user's priority to preserve the excellent outer silhouette. The SA10.39 cross-case research gate now expressly rejects any candidate whose off-owner RGB mismatch count increases, even when total image error decreases. Rejected candidate and its diagnostics were preserved as negative evidence.

### Accepted research-only solution

Instead of globally expanding the mask, emit **exactly 2 white top-boundary source-geometry stroke passes**, reusing the canonical original ring edges above, in the existing `<mask>` element. Each pass uses its two already-signed contour endpoints at x+0.5px, y+1.0px, with 1.25px white stroke for this **GC001-only Chrome calibration**. Its purpose is to match OpenCV's inclusive top row; it does not change the source scene, original owner contour data or apparel shape.

New code `tools/run_sa1038_vector_mask_browser.py` opt-in parameters:
```
--signed-top-edge-stroke 1.25 --signed-top-edge-y-shift 1.0
```
The default remains no selective stroke and production remains unchanged.

The implementation:
- Derives topmost **signed horizontal fill-ring segments**; refuses if no matching source top segment exists.
- Rasterizes the **unchanged authoritative existing owner**, and checks the union of selected source contour segments exactly reproduces the canonical top owner row, byte for byte. Fail closed if not.
- Never creates a novel garment or extends the original canonical contour coordinate set. **Two additional SVG paint paths and four reused contour endpoints** are explicitly counted, in addition to the **five existing parent-hole white boundary passes** (31 repeated ring-point occurrences).
- Prohibits simultaneously enabling global parent outline (silhouette-widening stroke) and this selective fix.
- Keeps the previous signed owner source rings, 5 materials/27 vertices, face, left/right arm, source observed colors and original primitive structure immutable.
- Does not embed input-image/PNG/bitmap or base64 or use generative fill.

### Verified real Chrome and two-image regression

After a genuine isolated Chrome headless rendering with SHA attestation:
- **45 differing pixels** vs SA10.38's 69: **34.7826% reduction**.
- Vs original SA10.37 clipPath 528: **91.4773% total reduction**.
- **3 off-owner** mismatches, same as original SA10.38, no new outside-source silhouette regression.
- Remaining **39** are paint/blank edge disagreements, **6** are color conflicts in jointly painted pixels.
- Boundary-distance audit: **14** near both original parent and material edge, **31** near material edge only, **0** unexplained away from these signed borders (within 1px morphology); **28** connected discrepancy components.
- The problem y=245 top row is now **0 mismatches**. Thus the remaining work is mostly material diagonal-edge raster parity, not missing clothing blocks.
- Two independent GC001 Chrome runs yielded **identical SHA256 for six artifacts** (SVG, HTML, canonical OpenCV raster, actual Chrome PNG, metrics and difference heatmap), and two independent signed residual-audit artifacts also matched **2/2 SHA256**.
- Negative image `Juufuutei-Raden` had a **distinct source SHA256**, and because this five-panel shirt/tie pattern does not match, it has **0 added wardrobe changes**, unchanged screenshot SHA. It is a negative control, **not** a second positive SVG cloth case.
- Two-real-source **research gate PASS** but **browser exact-pixel parity FAIL (45 != 0)**.
- Local original-gate and new focused regression **120 passed, 18 parameterized subtests passed**; GitHub Actions final research branch run to verify separately.

## Source, tests, and evidence

Files in canonical GitHub:
- `tools/run_sa1038_vector_mask_browser.py` (original signed parent vector mask, new selective source top edge option + real Chrome hashes)
- `tools/run_sa1039_svg_residual_audit.py` (owner/material border attribution, refuses forged screenshots, protects actual source pixel ownership)
- `tools/run_sa1039_edge_research_gate.py` (before-after audit, independent character control, rejects broad parent overpaint, explicit counted source outline draw passes)
- `tests/zerobase/test_sa1038_vector_mask_browser.py` (existing + selective top-edge proof)
- `tests/zerobase/test_sa1039_svg_residual_audit.py`, `test_sa1039_edge_research_gate.py`
- `.github/workflows/sa1032-svg-research.yml` (includes SA10.39 tests/compilation).

Machine-readable:
- [Current attested 45px Chrome rendering](evidence/sa1039_gc001_selective_top_actual_chrome_20261008.json)
- [Actual Chrome executable/source/screenshot SHA256 attestation](evidence/sa1039_gc001_attested_chrome_exec_20261008.json)
- [Current residual signed owner/material attribution](evidence/sa1039_gc001_selective_top_residual_20261008.json)
- [Previous baseline 69px attribution](evidence/sa1039_gc001_baseline_residual_20261008.json)
- [Rejected 56px broad silhouette overpaint attribution](evidence/sa1039_gc001_rejected_global_outline_residual_20261008.json)
- [GC001 and untouched Raden strict two-real-source research gate](evidence/sa1039_gc001_raden_strict_source_silhouette_gate_20261008.json)

Drive (all **23 artifacts SHA256 verified** plus manifest; correct parent `chatGPT及びCodex用/Minimalizer`):
[SA1039_SelectiveTopSVG_20261008](https://drive.google.com/drive/folders/1AkmQG5r-cEU9uDrUInkUAnQlaEl_D7k0)

Recommended visual:
`GC001_diagnostics/chrome_4way_528_69_45_reference.png`, showing the actual SA10.37 vs SA10.38 vs SA10.39 Chrome apparel layer next to canonical OpenCV target. Folder also contains original GC001 and Raden inputs, three groups of calibration measurements, old/rejected/new diagnostic reports, actual final SVG, screenshot and difference heatmap. No generated artwork was used for the actual material output.

## Hard release blocks (not waived)

1. **Exact browser SVG pixel parity still FAILS, 45 pixels.** The GC001 top-edge SVG calibration is not a universal browser coordinate rule, and the 3 out-of-owner pixels are *not* source-parity PASS. The research gate allows no **regression**, but production's exact gate remains stricter.
2. Original full source contour geometry still exceeds unchanged vector budget: **GC001 3,604 > 1,887; Raden 2,370 > 1,412**, before adding internal material 27 vertices and SVG stroke paint passes. Do not hide reused paths from actual rendered geometry count.
3. All Chrome SVG parity is currently measured on an **isolated apparel layer**, not whole-character z-order, face/arm overdraw or original complete silhouette.
4. Needs **a second independently matching apparel image** and more varied semantic materials. Raden is negative only.
5. **Human visual approval PENDING.** No merge to main, no production deploy.

**Disposition:** SA10.39 research and evidence preservation COMPLETE, **PR #223 stays draft and unmerged**. Next: tackle remaining 31 material-edge-only mismatches without widening source silhouette, true combined vertex reduction under source topology gates, and full browser-rendered character regression.
