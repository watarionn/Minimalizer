# Hair Tonal Ownership Scene (2026-10-09)

**Research PoC complete; full-character quality remains HOLD/NO-GO, production unchanged.**

This stage integrates hair's existing **source-owned part** via accurate pixel-cell contour tracking and source-observed palette, instead of blindly appending a giant monochrome orange layer over goggles and face.

The prior research-composite SVG from `BangsTwoPixelIntegration_20261008` keeps three previously verified 694-pixel central fringe tonal paths. This script, `tools/research/hair_tonal_ownership_scene.py`, identifies the *other* original hair SVG elements and replaces them **at the same DOM index/z-order**, using the original Phase04 mask and the existing source-medoid hair tone extraction. Face-misclassified 390px fringe is not added as broad solid hair: it stays separately covered by the three trusted colored fringe paths. No face/subject skin plane; no new raster embedded; no generative image processing.

Real GC001 original-source run: **5 hair tonal layers, 104 contours, 3,840 vertices**. The source-owned hair replacement changed **5,672 rendered RGB pixels**, all confined to the original observed hair mask plus 2px antialias margin (**0 changed outside**). All **3 verified fringe paths** remain. The source hair palette comprises colors drawn from actual original hair RGB pixels. The sprite still has incomplete blank face and fragmentary accessories/uniform. The hair look is more finely sectioned than the previous approximation, but remains visually rough, and no claim of full visual PASS is warranted.

Code regression `tests/test_hair_tonal_ownership_scene.py` plus previous hair/fringe/no-face-plate tests: **36 PASS**. No browser/Local/Public deployment.

Artifacts: `chatGPT及びCodex用/Minimalizer/HairTonalOwnershipScene_20261009`, Drive folder `1tynLfq_JcBioeZhi_V3AfMmcu2ZmDCTK`: the integrated `part_owned_tonal_hair_scene.svg`, before/after renders, comparison board, SHA manifest.

Next: diagnose why parts other than hair (goggles, clothing and the subject's unresolved face) are incomplete. Audit ownership and source-observed color clusters region by region; avoid any full-skin paint. Run independent second Golden case before production integration. This is a standalone research branch, not a Core release.
