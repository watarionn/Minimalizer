# Minimalizer 2.0 Calibration 05 Phase X

Status: Default Migration implemented and regression-verified locally on RDC.
Date: 2026-09-17

## Purpose

Phase X executes the explicitly approved browser Default Migration after the Phase U release-candidate dry run, Phase V pre-cutover gate, and Phase W cutover package.
The browser Standard default now uses Minimalizer 2.0 only for requests covered by the approved compatibility envelope.
Legacy API callers, specialized modes, and incompatible requests keep their established behavior.

## Cutover state

Browser migration contract current state: `v2_standard_default`.
Rollback target remains `legacy_default` and requires no data migration.
Automatic fallback after a V2 execution failure remains disabled.
The public browser continues posting to `/api/minimalize`; browser-originated default requests identify themselves with `X-Minimalizer-Browser-Default: v2`.
Direct callers of `/api/minimalize` without that browser marker remain legacy-routed.

## V2 default eligibility

A browser request routes to V2 only when all of the following hold:
- mode is `standard`
- level is the default `4`
- output is PNG
- background is white
- source has no material transparency
- no custom `colors` override
- no custom `max_shapes` override

The hosted V2 path is capped at `analysis_max_side=400` as required by the Phase T performance budget.
SVG, transparent/source backgrounds, transparent inputs, custom detail controls, Rinka Reference, and Color Strip stay legacy-routed.

## Browser behavior

Standard mode now previews PNG by default so the ordinary one-click browser path reaches V2 when eligible.
The default Standard background is white.
The result metadata indicates whether the request used `Minimalizer 2.0` or the legacy engine.
SVG remains available and is generated through the legacy compatibility route.

## Validation

Default-migration focused suite: `49 passed, 1 warning`.
V2 regression: `171 passed, 334 deselected, 1 warning`.
Full repository: `503 passed, 2 failed, 1 warning`.
The two full-suite failures are the unchanged missing fixture `tests/assets/false_face_phase85.png` failures:
- `test_rejected_face_skips_face_geometry_quality`
- `test_rejected_face_is_not_penalized_as_missing_face`

No Default Migration regression was found.
The focused suite also proves that a V2 execution error is surfaced and is not silently retried through legacy.

## Scope boundary

This phase changes local feature-branch code only.
No push, PR, main update, merge, deployment, or GitHub Actions execution occurred.
The remote feature branch therefore remains at the Phase T handoff until a later explicitly approved publish step.
