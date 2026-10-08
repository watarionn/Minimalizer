# Semantic Art Mixer v4: source-owned region palette / primitive economy trial (2026-10-08)

**Status: isolated experiment complete; shape/primitive-economy result NO-GO; no production release.**

## Why this tranche exists
The v3 D trial reliably preserved source masks for the hair, face, neck, uniform, arms, torso and accessories, but was too close to the original full-color raster and did not prove meaningful shape budget reduction. v4 studies a controlled per-part reduction with two visual modes and two palette limits. Prior v3 and all older Art Modes remain intact.

## How it works
- Code: `tools/research/semantic_art_mixer_v4_budget.py`; 5 offline tests in `tests/test_semantic_art_mixer_v4_budget.py`.
- Inputs: SHA-verified canonical GC001 original and existing Phase03 source subject + Phase04 face/hair/arms/neck/torso/clothing/lower-body/accessory masks, reusing v3 loader.
- Four options: 3-color palette with **flat one-color per part**, 3-color palette with **regional median**, 5-color palette with **flat**, 5-color with **regional median**. Hair, clothing and accessories receive a small extra capacity in the regional variants.
- Colors painted into part masks are snapped to **RGB triplets that appear in the corresponding original source part**. Face keeps the v3 three-band original-skin plane, and the green necktie uses the existing connected-original mask / exact RGB Color Lock.
- The rendering is raster **PNG only**. It has neither actual polygon simplification nor SVG output. The `raster_regions` counter is a count of connected equal-RGB regions *within all source foreground pixels*, NOT SVG primitives. Its large values also include untouched source pixels in residual unowned regions. Never advertise this counter as achieved vector reduction.
- Production engine, ZeroBase2/LocalWorker/Public and RRM are not changed.

## Actual GC001 comparison

| Variant | Raster connected color islands (proxy, not shapes) | Distinct foreground colors |
|---|---:|---:|
| E3 Flat | 3418 | 3095 |
| E3 Regional Median | 3974 | 3235 |
| E5 Flat | 3418 | 3095 |
| E5 Regional Median | 4269 | 3214 |

All four outputs generated. Gallery SHA-256: `a22a49fb456520645c7f966dea5d135e9a90c854a9d1a232f32059fe08251b6e`.

**Visual decision: NO-GO for Flat** (it recreates the familiar giant grey/brown torso trapezoid, collapses clothing and weakens goggles); **HOLD for Regional Median** (hair/goggles/uniform are much more readable, but large small-island noise and excessive raster fragmentation remain). Fewer colors in each part did **not** yield fewer whole-image regions because unowned residual areas still contain source pixel detail. The source exact silhouette/negative space is still based on preserved Phase03 owner mask, not newly inferred. We make no claim of improved arm/torso separation or exact SVG parity.

## Tests and evidence
- `python -W error tools/research/semantic_art_mixer_v4_budget.py --root <private Minimalizer Drive> --out <private output>` completed with four output images.
- V4 and earlier v1-v3 targeted tests: **31 PASS**.
- Source image and its masks are reused from verified private/repository paths. No ML inference, inpainting, hallucinated facial features or generated imagery.

Private output folder: `chatGPT及びCodex用/Minimalizer/SemanticArtMixer_v4_Budget_20261008/`, Drive ID `1gyo9_sjar3ht9TqriE1cXbAwvoo8PRW0`. Contains four variants, source-referenced gallery and JSON manifest. Google Drive *cloud-side synchronization* should be independently checked: mounted Drive file presence alone is not proof.

## Next gate (no automatic production rollout)
1. Keep v3 D as the reference for part ownership, **not as final minimal art**.
2. Build a source-mask ownership partition that covers **all** foreground pixels or explicitly handles residual color regions; residual full raster source pixels must not escape the complexity budget.
3. Within each **independent part mask**, build connected components and simplify them to countable **polygons/Bezier curves**, with rasterized source-mask IoU, exact foreground/nonforeground exclusion, left/right arm region survival, face boundary/no-eye gate, necktie original-color gate, and explicit total vertex/path budget. Reject if any hard gate fails.
4. Test on a distinct character source before selecting an art style for Local PWA. Do not promote this raster color-budget experiment to Local/Public UI.
