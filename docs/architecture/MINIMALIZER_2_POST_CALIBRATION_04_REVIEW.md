# Minimalizer 2.0 Post-Calibration-04 Visual Review

Date: 2026-09-15
Baseline branch: `feature/minimalizer-2-calibration-04-medium-detail`
Baseline HEAD: `141554ac4f682635a6288e9e0a5b07e10e7a63c1`
Calibration 04 engineering commit: `dc10ca1e6cd4daf2dddee6af41ca19a53f75188d`

## Purpose

Determine the dominant remaining visual mismatch against the 18 Approved Geometric References before starting Calibration 05.
This review deliberately avoids guessing another Detail Budget or Region Merge threshold.

## Corpus integrity

- Approved reference folder: `採用見本_幾何学ミニマル_20260911`
- Approved reference SHA-256 matches: `18 / 18`
- Current Minimalizer 2.0 regression cases: `18 / 18`
- hard invariant failures: `0 / 18`

The comparison uses the canonical input manifest and the approved images recorded in `tests/assets/approved18_manifest.json`.

## Visual finding

Calibration 04 successfully reduced medium-size color/style fragments, but the dominant remaining mismatch is not visual-group count.
The Approved References are built from large intentional polygonal planes with long straight boundaries.
Current output frequently preserves the correct broad color masses, but their visible boundaries are short, stair-stepped, and locally irregular.
## 18-case image measurements

Images were normalized to 320 x 320 and compared with the same diagnostic procedure.
The metric is diagnostic only; it is not a quality gate yet.

Mean current/reference ratios:
- edge density: `0.7503`
- long-line support: `0.3155`
- approximate polygon vertices: `1.3825`
- edge-contour count: `0.9483`

Every case had lower long-line support than its Approved Reference: `18 / 18`.
Every case had lower edge density than its Approved Reference: `18 / 18`.

This combination is important. Current output does not simply contain too many boundaries.
It contains fewer visible boundaries overall, while the boundaries that remain are more locally fragmented and less line-like.

The internal Calibration 04 corpus also shows:
- mean selected regions: `70.89`
- mean contour vertices: `5696.72`
- mean polygon primitives: `64.11`
- mean converted non-polygon primitives: `6.78`
- polygon share: `90.44%`

The high polygon share is not itself a defect. The problem is that these polygons inherit too much local contour detail instead of becoming deliberate planar facets.
## Representative cases

- Kikirara-Vivi: broad pink/purple/skin masses are recognizable, but hair and body boundaries remain locally jagged instead of forming long facets.
- Otonose-Kanade: small face/ribbon/clothing fragments remain visually noisy; the Approved Reference expresses the same subject with long angular planes.
- Koseki-Bijou: color hierarchy is broadly present, but hair, sleeve, and torso structure lacks the long planar divisions of the reference.
- Hakos-Baelz: a useful guard case because the Approved Reference is itself structurally rich; simplification must not mean deleting meaningful planes.
- Raora-Panthera: goggles and accessory structure show why blanket detail removal is unsafe. Important medium/large accessory planes must survive.
- Todoroki-Hajime: current output is already too flat despite Calibration 04 not acting on it. This proves that stronger Detail Budget collapse is not the next solution.

## Decision

Calibration 05 will target **Planar Polygonization / Long-Line Reconstruction**.

The goal is to turn visible region/group boundaries into a smaller number of intentional straight segments while preserving the visual planes that the Approved References rely on.
This is different from merely deleting vertices or collapsing more colors.

Calibration 05 must initially keep the established Region Merge tree and Calibration 04 Detail Budget behavior unchanged.
Do not globally lower visual-group targets.
Do not reopen Region Merge unless later evidence proves that a post-merge solution cannot produce the required planar structure.

Arbitrary angular polygons remain first-class output. Calibration 05 must not force the scene into rectangles, ellipses, or capsules just to increase primitive conversion rate.
## Calibration 05 first probes

Start with a diagnostic metric before changing production behavior:
1. measure visible-boundary straight-segment support after Detail Budget
2. distinguish long structural segments from short local zigzags
3. run smoke cases before the full corpus

Initial smoke set:
- Kikirara-Vivi: jagged broad masses
- Otonose-Kanade: small-fragment pressure
- Todoroki-Hajime: over-flattening guard
- Raora-Panthera: accessory-structure guard
- Hakos-Baelz: complex-reference and directional-loss guard

Any production probe must preserve:
- shared-boundary consistency
- topology and full coverage
- characteristic-anchor relationships
- protected palette relationships
- Contour IoU and directional guards
- Calibration 04 visual-group behavior unless explicitly justified

Acceptance should require hard invariant failures `0 / 18`, followed by V2 and full-repository regressions.
