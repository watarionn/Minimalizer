# GC001 Visor Source Boundary and RGB Audit, Pale Frame Refinement (2026-10-09)

**Research result: source-edge/RGB audit PASS; GC001-specific RGB refinement PASS; full-character Golden HOLD.** No production deployment or rewriting original masks.

## Why the prior self-mask coverage was not enough

PR286 implemented the source-reviewed one-piece visor: inner single lens 1,663 pixels, externally labeled frame 1,017 pixels, union 2,680 pixels, and a native 340px SVG vector matching 2,680/2,680 pixels of **its own hand-traced annotation**, with zero overflow. This was a vectorization correctness test, not independently observed semantic accuracy. This stage compares to the actual original source instead.

Source: GC001 Kyoko canonical SHA-256 `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`. Original high-resolution official Kyoko still acts only as an independent **one-piece visor topology reference** (different pose, not a geometric template). No generated image, color reconstruction of unseen pixels, or use of official 3D.

## Independent measurements

Script `tools/research/visor_source_boundary_rgb_audit.py` takes the **native source RGB** and actual resvg rendered PNGs, computes original-image Canny edge distance to manual outlines and per-role source RGB mean absolute error (MAE). It does **not** treat Canny edges as semantically correct goggles boundaries.

| Native source measurement | Lens | Frame | Outer visor |
| --- | ---: | ---: | ---: |
| Manual perimeter within 2.5px of some source Canny edge | 96.81% | 96.76% | 96.72% |
| Source warm/orange pixels in manually labeled role | 61.09% | **37.36%** | 52.09% |
| Source pale/silver pixels in manually labeled role | 22.61% | **45.23%** | 31.19% |
| SVG scene RGB MAE vs original **before PR286** | 20.676 | 32.448 | 25.143 |
| SVG scene RGB MAE vs original **after PR286** | **17.450** | **39.881 (worse)** | **25.962 (worse)** |

The manual frame was over-broad and included source orange/gold/hair-like regions. Canny proximity is encouraging geometric evidence but can match unrelated source reflection/hair/hat edges. Pixel-perfect boundary semantic correctness is **not proven**.

## Conservative correction, actual renders

Script `tools/research/visor_source_material_refinement.py` explicitly tests seven fixed material variants. Source values are read directly from the original and converted into candidate frame ownership *only within the prior frame annotation*, never the entire goggles ROI. Lens geometry stays unchanged. The v1 visor paths are replaced only in a research-only character scene; all three source-certified inter-eye bangs paths remain byte-identical and the frame never overflows the visor + 2px antialias guard.

Gate: material candidate must retain at least **40% of the previously annotated frame pixels**, improve **both** frame and total visor original-source RGB MAE, not degrade lens RGB error by more than 0.25, and change zero pixels outside original visor 2px antialias margin. Select lowest total visor RGB error, break ties by vertices. Tested baseline original 4 colors; orange-negative mask with frame palettes 4, 6, 8; source-pale mask with palettes 4, 6, 8.

Best research candidate: **`source_pale_palette4`**:
- Pixel ownership: **460 directly observed pale/white frame source pixels**, compared to previous over-inclusive 1,017 manual frame pixels. The other **557 previous annotation pixels are NOT certified hair** and are not newly painted white.
- Frame RGB MAE **39.881 → 29.097** (27.04% reduction).
- Full visor RGB MAE **25.962 → 21.871** (15.76% reduction); also better than pre-visor scene MAE 25.143 within the same annotated region.
- Lens RGB MAE **17.450 → 17.452**, effectively unchanged.
- Pixel-Cell vector complexity **920 → 656 vertices** (264 fewer, 28.70% reduction).
- Zero pixel changes beyond original visor + 2px AA neighborhood. All three certified inter-eye fringe paths remain untouched.
- Note: excluding the 557 non-pale source pixels is a *candidate material gate*, not final external semantic pixel labels or proof of correct hidden anatomy. Detailed comparison still shows loss of source micro-highlights and material variation. **Full Golden NO-GO**.

Actual source zoom comparison and material-mask overlaid galleries were visually inspected. No Local/Public/Worker code or deployment touched, no skin-colored full-face plate, no image generation, no hallucinated frame underneath hair.

## Validation and preservation

Targeted regression `tests/test_visor_source_boundary_rgb_audit.py` includes synthetic independent source Canny-distance vs shifted geometry, source RGB error independence from self-mask overlap, orange-hair exclusion, strict material selection failure tests, production and full Golden hold gates. Together with historical goggles/hair/no-face-plate suites: **83 PASS** in the isolated Windows research environment. Actual 7-variant SVGs/PNGs and SHA manifest are stored in the approved private Drive `chatGPT及びCodex用/Minimalizer/VisorSourceBoundaryRGBAudit_20261009`, folder ID `1MEHiAnrpqEX6JMUGAO0ysOYjEZxrW_A4`.

## Next

Do not tune additional GC001 color thresholds without a separate independent holdout. On another *source-verified character*, test whether source-material ownership and edge validation generalize. Then return to the main whole-character deficit (face visibility with no synthetic skin plane, clothing, arms) instead of indefinitely polishing a local visor. Never declare production PASS from native source self-mask IoU.
