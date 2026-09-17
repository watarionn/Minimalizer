# Minimalizer 2.0 Calibration 05 Phase Y Release Preparation

Date: 2026-09-17
Status: locally release-ready; remote publish not yet approved.

## Proposed PR title

`Migrate eligible browser Standard PNG requests to Minimalizer 2.0`

## Proposed PR summary

This change promotes Minimalizer 2.0 to the browser Standard default only inside the compatibility envelope proven by Calibration 05.
Eligible default level-4, white-background, opaque Standard PNG requests route to V2 with the hosted 400px analysis cap.
SVG, alpha-sensitive requests, custom detail controls, direct legacy API callers, Rinka Reference, and Color Strip remain on established legacy routes.
V2 errors are surfaced and are never silently retried through legacy.

## Verification to cite

- Phase X focused migration gate: `49 passed, 1 warning`
- Phase X V2 regression: `171 passed, 334 deselected, 1 warning`
- Phase X full repository: `503 passed, 2 known missing-asset failures, 1 warning`
- Phase Y default-migration endpoint tests: `10 passed, 1 warning`
- Phase Y expanded focused suite: `47 passed, 1 warning`
- Phase Y real Uvicorn HTTP acceptance: PASS

The two full-suite failures remain caused only by missing `tests/assets/false_face_phase85.png`.

## Rollback procedure

Rollback is a routing-state change only:
1. set browser migration `current_state` to `legacy_default`
2. verify `/api/v2/info` reports `legacy_default`
3. send a browser-marked Standard PNG request and confirm `X-Minimalizer-Route: legacy`
4. confirm Rinka Reference and Color Strip remain unchanged
5. no stored output conversion or data migration is required

Do not add automatic V2-to-legacy retry as part of rollback.
Do not change visual thresholds, SLIC target, Region Merge cost, facet acceptance, or preset semantics during rollback.

## Publish safety

Before any remote push, inspect `.github/workflows` and confirm the push target will not trigger metered GitHub Actions.
Do not push directly to `main`.
Create/refresh a feature branch first, then a Draft PR only after explicit user approval.
Ready-for-review, merge, and deployment each remain separate approval boundaries.

## Post-deploy smoke checks

After an explicitly approved deployment:
- Standard one-click opaque PNG should report V2
- Standard SVG should report legacy
- transparent Standard PNG should report legacy
- direct legacy API caller without browser marker should report legacy
- Rinka Reference and Color Strip should report legacy
- V2 default response should report configured analysis max side `400`

## CI readiness

`.github/workflows/ci.yml` was reviewed and updated locally.
Current triggers are PR events and pushes to `main`; a feature-branch push by itself does not run the workflow.
Before Phase Y, CI still expected Web `0.8.0`, Rinka `phase10`, and pre-characteristic Color Strip metadata, so a PR could have failed for stale CI reasons.
Those expectations now match Web `0.13.0`, Rinka `phase16`, and current Color Strip modes.
The workflow also includes the Default Migration test suite and a real-server V2-default smoke request.
The Rinka evaluation guard was moved to Phase 16 while retaining established structural/identity/silhouette safety checks; obsolete aggregate reduction thresholds were removed without inventing replacement thresholds.

Local workflow validation passed: YAML parse, 16-case Rinka Phase 16 evaluation guard, Web/API/UI command (`49 passed`), and real-server V2 smoke.
No GitHub Actions run was started during this preparation.
