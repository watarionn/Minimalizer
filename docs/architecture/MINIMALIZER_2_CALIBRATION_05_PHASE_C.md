# Minimalizer 2.0 Calibration 05 Phase C

Updated: 2026-09-15
Status: diagnostic / probe phase completed
Branch: `feature/minimalizer-2-calibration-05-planar-polygonization`

## Goal

Phase C investigates the remaining gap after Phase B Shared-Boundary Line Fitting.
The 18 approved geometric references are used as comparison material.
Production Region Merge, Detail Budget targets, and palette targets are unchanged in this phase.

Phase C adds observational macro-facet diagnostics:
- `macro_facet_count`
- `macro_large_facet_share`
- `macro_mean_vertices`

The diagnostics quantize rendered RGB in fixed bins, find connected color components above a normalized area threshold, and approximate each component polygon for a comparable facet-complexity measurement.
They do not affect `algorithm_digest` or production rendering.
## 18-case macro-facet comparison

References were normalized to the current output size before measurement.
18-case means:

| metric | current Phase B | approved reference |
| --- | ---: | ---: |
| macro facet count | 31.56 | 67.00 |
| large-facet area share | 0.8850 | 0.6394 |
| area-weighted mean vertices per facet | 9.75 | 7.80 |

This reverses the naive assumption that the current output still has too many visible planes.
The current output has fewer, larger, and more complex visible color components.
The references use more distinct planes, but each plane is more deliberately polygonal.

Todoroki-Hajime is the clearest guard: current macro facet count is `13`, while the approved reference measures `61` under the same diagnostic.
Therefore additional blanket style collapse would move the image in the wrong direction.
## Stage decomposition

Using the same macro-facet diagnostic on Phase B artifacts:

| stage | mean facet count | mean large share | mean vertices |
| --- | ---: | ---: | ---: |
| Primitive | 35.72 | 0.8729 | 9.83 |
| Palette | 36.00 | 0.8711 | 9.66 |
| Detail Budget | 31.61 | 0.8834 | 9.65 |
| Final | 31.56 | 0.8850 | 9.75 |
| Approved Reference | 67.00 | 0.6394 | 7.80 |

Detail Budget removes roughly four visible facets on average, but most of the reference gap already exists before Detail Budget.
Therefore Phase C must not be reduced to undoing Calibration 04.

The selected-region count is about seventy in the canonical corpus, close to the reference macro-facet count. This indicates useful geometric capacity already exists in the selected-region topology, even though current palette and rendering decisions fuse much of it into large visible blobs.
## Source-color facet probe

A diagnostic-only probe blended each selected region's source color slightly back toward its current effective palette color while keeping the existing geometry.
The best conservative smoke setting was then checked across all 18 cases:
- blend factor: `0.18`
- minimum region area ratio: `0.002`

18-case means moved to:
- macro facet count: `36.33`
- large-facet area share: `0.8580`
- mean facet vertices: `9.58`
- long-line support: `0.23525`

Phase B baseline long-line support was `0.23542`, so the source-color probe produced no meaningful line-quality gain.
It reveals some hidden planes, especially in complex cases, but does not reconstruct the deliberate triangle/trapezoid-style macro geometry seen in the approved references.

The source-color blend is therefore rejected as a production solution. It remains evidence that selected-region boundaries can support additional visible facets without reopening Region Merge.
## Regression

Canonical 18-case visual regression after adding the diagnostics: hard invariant failures `0 / 18`.
V2 regression: `111 passed`.
Full repository: `443 passed, 2 failed, 1 warning`.
The two failures are the existing missing `tests/assets/false_face_phase85.png` failures.
No production output behavior changed in Phase C.

## Decision

Phase C establishes that the next solution must reconstruct visible macro facets, not globally remove more detail and not merely restore source color variation.

Recommended next engineering step: Calibration 05 Phase D, **Selected-Region Planar Facet Reconstruction**.
Start with a post-Detail-Budget candidate graph built from selected-region topology and effective visual groups. Use existing shared boundaries as candidate facet seams, choose only structurally justified seams, and simplify each visible facet toward a small polygon while preserving coverage and important relationships.

Initial constraints for Phase D:
- keep the Region Merge tree unchanged
- keep Calibration 04 Detail Budget target ranges unchanged
- do not add arbitrary checkerboard shading or per-image special cases
- use macro-facet diagnostics and long-line support together; neither is a single-objective target
- preserve characteristic anchors and protected palette relationships
- Todoroki-Hajime remains the over-flattening guard
- Raora-Panthera and Hakos-Baelz remain accessory/complex-structure guards
