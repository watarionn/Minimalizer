# Goggle Stroke Material Classification (2026-10-09)

**Source-only material hypotheses completed; verified goggles lens/frame contours remain HOLD. Production unchanged.**

Canonical GC001 source and the frozen source-edge trace JSON were reused, without repeating Canny, model inference or changing any mask. The 38 review edges selected in PR276 were classified by actual on-curve original RGB / HSV samples using conservative thresholds. Outcome: **22 likely hair or warm material**, **6 possible white frame**, **10 uncertain lens/frame**, **0 verified goggles strokes**. No confident standalone reflection role was identified.

Color-derived categories are only material hypotheses. Orange lens reflections and orange hair can share hues. A white edge might be goggles frame, glare, clothing or neighboring hat. Visual source overlay shows that the six possible white-rim candidates cover fragments but do not establish complete, connected, separate goggles contours. In particular, do NOT fill or close the paths, claim successful left/right semantic goggles segmentation, or overwrite certified bangs.

`tools/research/goggle_stroke_material_classification.py` emits only isolated **unfilled SVG diagnostic polylines** annotated as unverified and a source comparison PNG. `tests/test_goggle_stroke_material_classification.py` and previous related Golden research: **61 tests PASS**.

Preserved under canonical private Drive `chatGPT及びCodex用/Minimalizer/GoggleStrokeMaterialClassification_20261009`, ID `1v4zfl-V3vqk6FWZu4o9-tRjriGePsStS`. Files: `stroke_material_hypotheses.png`, `diagnostic_material_strokes.svg`, `manifest.json`.

**Next:** final semantic human verification of specific goggle source curves (white rim, colored lenses, hair, highlights) and source-owned visible pixel component masks. No repeated generic ROI/color-based experiments without new evidence. Full character remains NO-GO; Local/Public untouched.
