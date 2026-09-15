# Minimalizer 2.0 Calibration 05 Phase E

Status: facet scene representation and conservative rendering gate implemented; normal production rendering remains unchanged.

## Goal

Phase D created deterministic planar-facet candidates but deliberately kept them out of SceneModel rendering.
Phase E defines how an accepted facet is represented and which candidates are safe enough to retain for a later renderer.

The gate must improve planar structure without materially damaging long-line support, protected palette relationships, coverage, or guard-case identity.

## Scene representation

`SceneModel` now has a separate `facet_overlays` collection.
A facet overlay references an existing region and does not create a new coverage region, palette assignment, or primitive.

`PlanarFacetOverlay` stores:
- source `region_id`
- variant RGB
- normalized split line `(a, b, c)`
- selected split side

Base `SceneShape` coverage remains unchanged.
The regression/debug renderer renders facets only when `include_facets=True`; its default remains `False`.
## Rendering gate

Minimal preset uses a greedy candidate-by-candidate gate.
Candidates are evaluated in deterministic order: stronger source-gradient evidence first, then larger overlay area, then region id.

An accepted candidate must satisfy all of the following:
- macro-facet count must not decrease,
- large-facet share may increase by at most `0.002`,
- mean vertices/facet may increase by at most `0.10`,
- it must provide at least one macro improvement,
- final long-line support may not fall more than `0.005` below the baseline scene,
- palette relationships with protection >= `0.75` must retain at least `75%` of their current contrast,
- significant original lightness ordering (`|DeltaL| >= 12`) must not flip.

Macro improvement means at least one of:
- facet count increases,
- large-facet share falls by at least `0.002`,
- mean vertices/facet falls by at least `0.05`.

Region Merge, Hierarchy Cut, Primitive Fitting, Palette Consolidation, and Detail Budget targets are unchanged.
## Canonical 18-case gate result

Using the canonical regression loader and the Phase E default gate:
- mean accepted facets: `0.7222` per image,
- mean macro facet count: `31.5556 -> 32.5000`,
- mean large-facet share: `0.88499 -> 0.87684`,
- mean vertices/facet: `9.7450 -> 9.6163`,
- mean long-line support: `0.235422 -> 0.240738`.

The gate is intentionally conservative. Some difficult cases accept no facet at all rather than spend structural safety margin.
Examples with zero accepted facets include Kikirara-Vivi, Otonose-Kanade, Raora-Panthera, and Todoroki-Hajime under the current defaults.
Hakos-Baelz accepts five facets while improving its measured long-line support.

Scene overlay count matched the accepted gate count in `18 / 18` cases.
Hard invariant failures remained `0 / 18`.

Normal final PNG output remained byte-identical to Phase D: SHA-256 matched `18 / 18` cases.
## Regression status

Focused facet/regression tests: `16 passed`.
V2 regression: `118 passed`.
Full repository: `450 passed, 2 failed, 1 warning`.

The two failures are the existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Minimalizer 2.

## Decision

Keep the facet rendering gate and `SceneModel.facet_overlays` as first-class internal structures.
Do not enable facet overlays in normal production rendering yet.
Do not relax the `0.005` long-line-loss budget in this phase.
Do not add per-character exceptions.

Recommended next step: **Calibration 05 Phase F: Opt-in Facet Rendering / Visual Acceptance**.
Phase F should render accepted overlays explicitly for the canonical 18 cases, compare them against the approved three-column visual references, and decide whether the gated overlays are visually good enough to become the default Minimal rendering path.