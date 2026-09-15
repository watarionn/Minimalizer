# Minimalizer 2.0 Calibration 05 Phase D

Status: candidate-generation stage implemented and validated; not wired to production rendering.

## Goal

Phase C showed that the current Minimal output has too few visible planar facets, while the Approved References use more, simpler geometric planes.
Phase D therefore tests whether existing selected regions can support additional planar facets without reopening Region Merge or lowering Detail Budget targets.

The production scene must remain unchanged until the candidate geometry has passed corpus-level validation.

## Canonical input rule

All corpus measurements in this document use the regression loader `load_rgb_file()`.
It composites alpha against white before processing and is the canonical comparison path.

Earlier ad-hoc probes that used `cv2.imread(..., IMREAD_COLOR)` are exploratory only and must not be used as canonical corpus numbers.
## Implemented stage

New module: `minimalize_engine/v2/facet/`.

The stage returns `PlanarFacetResult` containing zero or more `PlanarFacetCandidate` objects.
It is currently observational: `SceneModel` continues to use the original primitive geometry and effective palette assignments.

For Minimal preset, a region can become a candidate only when:
- it is visible after Detail Budget,
- selected-region area ratio is at least `0.012`,
- it is not tagged as a critical face/eye/mouth/hand semantic region,
- a luminance plane can be fit to its source Lab-L samples,
- the 90th-to-10th percentile predicted luminance range is at least `5.0`,
- each source-side of the split contains at least `25%` of the selected-region samples,
- each overlay-side contains at least `20%` of the selected primitive geometry.
The variant side is whichever side is farther from the effective palette luminance.
Its candidate color is a conservative blend of `78%` effective palette RGB and `22%` source-region representative RGB.
The resulting RGB displacement must be at least `4.0` in Euclidean RGB distance.

The split line, variant side, variant RGB, candidate area ratio, source gradient range, and source-to-base DeltaE are retained as deterministic candidate data.

No region is added or deleted. No primitive is replaced. No palette relationship is changed. No Detail Budget action is changed.

## Canonical 18-case candidate statistics

Hard invariant failures: `0 / 18`.
Mean candidate count: `4.8889` per image, range `0..10`.
Mean candidate overlay area ratio: `0.07520`.
Mean source gradient range among candidates: `9.1528` Lab-L units.

The five guard/smoke cases under the canonical loader produce candidate counts:
- Kikirara-Vivi: `9`
- Otonose-Kanade: `3`
- Todoroki-Hajime: `2`
- Raora-Panthera: `8`
- Hakos-Baelz: `6`
## Hypothetical overlay evaluation

The stage was also rendered experimentally without changing the production scene contract.
Across the canonical 18-case corpus:
- macro facet count: `31.5556 -> 34.1667`
- large-facet area share: `0.88499 -> 0.86538`
- mean vertices per facet: `9.7450 -> 9.6087`
- long-line support: `0.235422 -> 0.233668`

The long-line support change is about `-0.75%`, substantially smaller than the improvement in facet structure.
The Approved References measure approximately `67.7222` facets, `0.64227` large-facet share, and `7.1319` vertices per facet under the same canonical loader and metric configuration.

This means the candidate direction is useful but still far from the reference geometry.
It is not yet safe to make the overlays part of production output.
## Regression status

Focused facet/regression tests: `13 passed`.
V2 regression: `115 passed` with no Phase D warnings.
Full repository: `447 passed, 2 failed, 1 warning`.

The two failures are the existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Minimalizer 2.

Production-output immutability was checked against the Phase C canonical outputs: final PNG SHA-256 matched `18 / 18` cases.

## Decision

Keep the Planar Facet Reconstruction stage as a first-class candidate-generation stage.
Do not wire its overlays into `SceneModel` yet.
Do not reopen Region Merge, lower Detail Budget targets, or add per-character special cases.

The next phase should design the scene representation and acceptance gate for facet overlays so that a candidate can be rendered only when it improves planar structure without materially damaging long-line support, topology, protected relationships, or guard-case identity.

Recommended next step: **Calibration 05 Phase E: Facet Scene Representation / Rendering Gate**.
