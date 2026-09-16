# Minimalizer 2.0 Calibration 05 Phase S

## Browser UI Migration / Rollback Contract

Phase S resolves the `browser_ui_migration` readiness blocker without changing the production browser default.

The browser remains legacy-routed in this phase. The work defines a machine-readable rollout and rollback contract that a later approved UI switch can consume.

## Contract

Schema: `minimalizer-v2-browser-migration-v1`

Current rollout state: `legacy_default`.

Endpoints:
- legacy: `/api/minimalize`
- V2: `/api/v2/minimalize`

Specialized modes remain pinned to legacy:
- `rinka_reference`
- `color_strip`

No persistent data migration is required for rollback, and Phase S forbids silent automatic fallback after a V2 execution error.

## Rollout stages

1. `legacy_default`
   - current production behavior
   - Standard, Rinka Reference, and Color Strip all use legacy
   - no V2 selector is exposed

2. `v2_standard_opt_in`
   - Standard keeps legacy as default
   - an explicit V2 selector may be exposed
   - specialized modes remain legacy
3. `v2_standard_default`
   - eligible Standard PNG requests default to V2
   - incompatible Standard requests route to legacy
   - specialized modes remain legacy

Rollback always targets `legacy_default`.

## Eligibility composition

The browser contract does not duplicate format or alpha behavior. It composes the Phase Q and Phase R contracts.

A future Standard request is V2-eligible only when all are true:
- rollout state permits V2
- output format is PNG
- background mode is white
- source has no material transparency
- ignore-source-alpha is not requested

SVG, transparency-sensitive requests, source/custom/transparent backgrounds, and unsupported cases remain legacy-routed.

## Current browser protection

`web/static/app.js` remains unchanged by Phase S and still posts to `/api/minimalize`.

A regression test asserts that the current browser bundle contains the legacy endpoint and does not contain a direct `/api/v2/minimalize` fetch.

`/api/v2/info` now exposes the browser migration contract additively. Existing legacy `/api/info` semantics are unchanged.

## Rollback rules

Rollback is a routing-state change, not a data migration.
- set rollout state to `legacy_default`
- all browser modes immediately route to the established legacy endpoint
- no stored output or user data conversion is needed
- Rinka Reference and Color Strip never depend on the V2 rollout state
- V2 execution errors are surfaced rather than silently retried through legacy
## Validation

Focused browser/migration tests: `6 passed`.

The focused checks cover:
- rollout schema and stage order
- specialized-mode legacy pinning
- opt-in selector semantics
- Phase Q format routing composition
- Phase R alpha/background routing composition
- current browser bundle remaining legacy-routed
- `/api/v2/info` exposing the contract without changing `/api/info`

Phase S does not alter the V2 image pipeline, preset semantics, renderer, deterministic PNG bytes, alpha behavior, or current browser request endpoint.

## Migration readiness

After Phase S:
- `browser_ui_migration`: ready
- remaining blockers: `1`
- remaining blocker: `performance_budget`
- `ready_for_default`: still `false`

No production default is changed merely because the UI migration contract is ready.

## Next phase

Proceed to Phase T: Performance Budget Contract / Default-Migration Gate.

Phase T must define a representative latency/resource budget and evaluate the current post-Phase-N V2 measurements against that explicit budget. It must not declare readiness by inventing a threshold after seeing the result; the budget must be justified and recorded before the final migration decision.

## Regression status

- V2 suite: `146 passed`
- full repository: `482 passed, 2 failed, 1 warning`
- the two failures are the unchanged missing-asset failures for `tests/assets/false_face_phase85.png`
- no new regression was introduced by Phase S
