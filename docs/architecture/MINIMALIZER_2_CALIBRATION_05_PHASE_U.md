# Minimalizer 2.0 Calibration 05 Phase U

Status: release-candidate dry run passed locally on RDC.

## Purpose

Phase U verifies the already-defined browser migration route before any default cutover.
It does not change the production browser default, visual thresholds, SLIC targets,
Region Merge costs, facet acceptance, main, deployment, or rollout state.

## Dry-run contract

The simulated rollout state is `v2_standard_opt_in`.
Only an explicitly selected, eligible Standard PNG request routes to V2.
SVG, transparency-sensitive requests, source/transparent backgrounds, and
ignore-source-alpha semantics remain legacy-routed.
`rinka_reference` and `color_strip` remain pinned to legacy.
Changing the simulated state back to `legacy_default` returns every tested route to legacy.

## Verification

Focused Phase U + migration/output/alpha/performance/Web suite: `49 passed, 1 warning`.
V2 regression including the new Phase U tests: `158 passed, 1 warning`.
Full repository regression: `490 passed, 2 failed, 1 warning`.
The two failures are the unchanged missing `tests/assets/false_face_phase85.png` cases.
No new regression was observed.

## Release-candidate result

Phase U dry-run result: PASS.
The migration route is release-candidate verified for an explicit future cutover decision.
The browser remains `legacy_default`; no production cutover has occurred.
