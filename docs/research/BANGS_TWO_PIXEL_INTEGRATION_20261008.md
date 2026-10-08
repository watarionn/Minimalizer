# Bangs Two-Pixel Audit & Part-Scene Integration (2026-10-08)

**Status: isolated verified fringe integration completed. Full-character quality NO-GO. No production modifications.**

## Inputs and purpose
The GC001 inter-eye connected orange fringe is a verified 694-source-pixel region. Prior Pixel-Cell boundary experiment achieved 692/694 (99.71%) with only 288 SVG vertices, zero pixels outside the actual source region. This experiment identifies the two remaining missing pixels and independently stitches the verified local SVG into the prior source-owned whole-character SVG whose broad skin subject underlay was already removed.

All source imagery, selected `eps_0p35.svg` and masks were loaded from the verified private Drive/repository and the prior source file's SHA-256 was checked against the saved manifest. The full-character base remains the earlier known **incomplete face-hole scene**; do not confuse stitching hair with resolving that scene.

## Actual run
Code: `tools/research/bangs_two_pixel_integration.py`.

Two missing pixels are identified in source coordinates stored as **(y,x)**:
- (130,175), equivalently (x=175,y=130)
- (131,177), equivalently (x=177,y=131)

The source hair-only alpha is still **692/694**, with **0 excess**. These two points were **diagnosed, not synthesized or patched** in this stage. Three existing source-observed hair color SVG paths are appended to the archived non-skin-underlay subject vector scene. The full 340×340 subject render changed at **704 pixels**, all inside the observed fringe's 2-pixel antialiasing neighborhood; outside-region changes **0**. Existing face/subject opaque SVG plate and embedded raster remain prohibited. There is no face or skin cover and no image generation.

Visual evidence: the cropped central/right orange strand is substantially more continuous in the whole-character SVG than before, but the character still has a large empty face hole, fragmented uniform and gaps in the larger hairstyle. **Visual full-character quality NO-GO**, not deployable to MinimalizerLocal or MinimalizerPublic.

## Artifacts and verification
Private Drive location: `chatGPT及びCodex用/Minimalizer/BangsTwoPixelIntegration_20261008/`; folder ID `1Ef3QxUPW5MZgGtaafVrjdNEEl7SQvrwY`. Includes `verified_fringe.png`, `subject_before_bangs.png`, `subject_with_verified_bangs.svg`, `subject_with_verified_bangs.png`, `compare_integrated_bangs.png`, and `manifest.json` with SHA-256 provenance.

`tests/test_bangs_two_pixel_integration.py` and earlier face-plate/bang regression suites: **31 PASS**.

## Next
If preserving the 288-vertex budget is necessary, examine the final 2 source pixels with a constrained pixel-cell corner representation and accurate byte-level raster gate; do not manufacture a new lock-colored face or extrapolate a hair strand. Then improve the broader original part geometry/skin and garments separately with all semantic Golden gates. No production rollout is authorized by this local win.
