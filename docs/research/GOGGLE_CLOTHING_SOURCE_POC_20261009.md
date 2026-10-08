# Goggle Observation Window + Source-Tonal Clothing PoC (2026-10-09)

**Status: clothing original-color Pixel-Cell composition executed, research only; goggles segmentation unverified, full-character Golden HOLD.**

The prior GC001 investigation proved the saved `accessory_or_held_object` mask (217 pixels located at x=180..200,y=214..244) is NOT the goggles. Therefore this stage saved an explicit **goggles observation window** (x=104..240,y=38..103), but **did not present it as a segmented goggles mask**. The region contains 6,701 distinct original RGB values and is mixed goggles, hair, clothing/hat, background etc. No new goggles SVG part is generated; a genuine observer/annotated segmentation is still needed.

Clothing source geometry was already verified via independent Pixel-Cell source masks. This experiment replaces previous `major_clothing` and `lower_body` SVG layers in their original z-order using source-medoid color regions and Pixel-Cell epsilon 0.35. The resulting GC001 full-part research scene has **9 new clothing tone layers, 2,815 total vertices**, with **14,409 RGB pixels changed relative to old composited SVG**, all within the original source-owned clothing/lower-body masks + 2px antialias neighborhood. **0 changes outside**. The three previously certified source-fringe hair SVG layers are preserved. All newly selected clothing RGB values originate from actual pixels in the corresponding source part masks.

Actual before/after visual inspection: navy/white shirt pattern and several small decorations retain more texture and distinctions, but the image is still fragmented and the face is a large blank hole. This is not a finished character, nor confirmed goggles recognition, and must not be deployed to MinimalizerLocal or Public. No broad skin-colored face plate, inferred material, raster embedding or generative editing.

Scripts: `tools/research/goggle_clothing_source_poc.py`; `tests/test_goggle_clothing_source_poc.py`. The complete related regression suite **42 PASS**.

Approved canonical private Drive folder `chatGPT及びCodex用/Minimalizer/GoggleClothingSourcePoC_20261009`, ID `1-Qw1p9rztig8WYT0IQ5Udx8KGw5IIXDI`, contains actual scene SVG, before/after PNG, comparison image, original-source observation window PNG and SHA manifest.

Next work: independently segment real goggles from original pixel evidence, validate goggles/hair/front-back layering, and independently reproduce genuine skin regions from original visible source without guessing under facial features. Use a second Golden subject before generalizing style rules.
