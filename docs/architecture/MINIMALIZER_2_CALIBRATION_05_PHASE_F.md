# Minimalizer 2.0 Calibration 05 Phase F

Status: accepted facet overlays visually audited, shape quality guard added, and V2 renderer promoted to facet-aware default rendering.

## Goal

Phase E proved that a conservative numeric gate could retain a small set of planar facet overlays without damaging hard invariants. Phase F verifies that those accepted overlays also look directionally correct against the canonical Approved References before they become the default V2 rendering behavior.

This phase does not integrate Minimalizer 2.0 into the legacy CLI or Web application. Those entry points still use the legacy `minimalize()` pipeline and require a later integration phase.

## Visual audit

Canonical review layout:

`SOURCE | PHASE E BASELINE | PHASE F FACET | APPROVED REFERENCE`

The first Phase E gate accepted 13 overlays across 7 of 18 cases. Enlarged difference crops exposed two visually poor horizontal strip facets in Isaki-Riona. The problem was geometric rather than character-specific.
## Shape-quality guard

The two rejected Isaki overlays were separable from every other accepted overlay by common geometry criteria:
- minimum overlay short side: `0.0416` and `0.0333` of image diagonal,
- aspect ratio: `3.50` and `5.06`.

Every other accepted overlay had:
- short side >= `0.0645` of image diagonal,
- aspect ratio <= `2.13`.

Phase F therefore adds two global guards, with no per-character exception:
- reject an overlay when its bounding-box short side is `< 0.05 * image diagonal`,
- reject an overlay when its bounding-box aspect ratio is `> 3.0`.

Gate reasons are `overlay_too_thin` and `overlay_too_elongated`.
## Canonical 18-case result

With the Phase F shape guard and the canonical loader:
- accepted overlays: `11` total across `6 / 18` cases,
- mean accepted overlays: `0.6111` per image,
- mean macro facet count: `31.5556 -> 32.3889`,
- mean large-facet share: `0.88499 -> 0.87740`,
- mean vertices/facet: `9.7450 -> 9.6193`,
- mean long-line support: `0.235422 -> 0.239194`,
- hard invariant failures: `0 / 18`.

Accepted cases are Aki-Rosenthal `1`, Gigi-Murin `1`, Hakos-Baelz `5`, Koganei-Niko `1`, Shiori-Novella `1`, and Shishiro-Botan `2`.

The difficult guard cases Kikirara-Vivi, Otonose-Kanade, Todoroki-Hajime, and Raora-Panthera remain at zero accepted overlays under the current gate.
## V2 renderer contract

`minimalize_engine.v2.render_scene()` is now the public V2 raster renderer.

Default behavior renders accepted `SceneModel.facet_overlays`. Passing `include_facets=False` reproduces the Phase E baseline rendering and remains available for diagnostics and A/B comparison.

The regression/debug renderer now delegates to this shared V2 renderer, so canonical visual regression measures the same rendered representation that V2 consumers receive by default.

This does not change the legacy `minimalize_engine.minimalize()` renderer path. The current CLI and Web service still call the legacy engine and are intentionally out of scope for Phase F.
## Regression status

Focused facet/regression tests: `18 passed`.
V2 regression: `120 passed`.
Full repository: `452 passed, 2 failed, 1 warning`.

The two failures are the existing missing-asset failures for `tests/assets/false_face_phase85.png` and are unrelated to Minimalizer 2.

## Decision

Adopt the Phase F shape guard and make accepted facet overlays the default for the V2 raster renderer. Keep `include_facets=False` as an explicit baseline/debug opt-out.

Do not add character-specific exceptions. Do not relax the Phase E long-line budget. Do not wire Minimalizer 2.0 into the legacy CLI/Web in this phase.

Recommended next step: **Calibration 05 Phase G: V2 Rendering Closure / Export Contract**. Define a stable V2 output/export contract, verify deterministic PNG output and metadata, and prepare a separate later integration gate for CLI/Web without changing legacy production behavior yet.
