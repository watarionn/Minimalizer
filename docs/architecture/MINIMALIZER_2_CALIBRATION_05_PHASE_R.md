# Minimalizer 2.0 Calibration 05 Phase R

## Alpha / Background Compatibility Contract

Date: 2026-09-16
Scope: resolve the `alpha_background_parity` migration blocker without changing canonical opaque V2 rendering.

## Decision

Adopt a conservative compatibility-routing contract.
V2 is native only for requests that are already equivalent to its current renderer:

- source has no material transparency
- requested background is `white`
- ignore-source-alpha behavior is not requested

All alpha-sensitive or background-specific behavior remains on the legacy renderer.
This is a routing contract, not a claim that V2 now natively renders alpha.

## Routing policy

The Phase R machine-readable contract routes:

- opaque source + white background -> `v2`
- source with material transparency -> `legacy`
- `background=source` -> `legacy`
- `background=transparent` -> `legacy`
- `background=custom` -> `legacy`
- ignore-source-alpha requested -> `legacy`

## Why routing is used

The current V2 file adapter composites RGBA input onto white RGB before analysis, and the V2 renderer emits an opaque white RGB canvas.
Legacy behavior already carries the richer alpha/background contract, including source-derived, white, transparent, custom, and ignore-alpha semantics.

Implementing partial alpha output inside V2 in this phase would risk changing canonical region statistics, geometry, facet decisions, or PNG bytes. The compatibility route preserves those behaviors instead.

## Exact opaque-path proof

A focused fixture was written once as RGB PNG and once as fully opaque RGBA PNG.
Both inputs were sent through `minimalize_file_png()` with the same preset and filename.

Results were exactly identical for:

- exported PNG bytes
- rendered pixel SHA-256
- deterministic PNG SHA-256

Therefore adding the Phase R contract does not change the native opaque-white V2 path.

## Migration result

`alpha_background_parity` changes from `blocked` to `ready`.
The migration gate now has two blockers:

1. `browser_ui_migration`
2. `performance_budget`

## Validation

Focused alpha/background + migration tests: `6 passed`.
V2 regression: `142 passed`.
Full repository regression: `478 passed, 2 failed, 1 warning`.

The two failures are the pre-existing missing `tests/assets/false_face_phase85.png` failures and are unrelated to Phase R.

Canonical artifacts:

- `MINIMALIZER_2_CALIBRATION_05_PHASE_R_ALPHA_BACKGROUND.json`
- `MINIMALIZER_2_CALIBRATION_05_PHASE_R_READINESS.json`

## Next engineering step

Proceed to **Calibration 05 Phase S: Browser UI Migration / Rollback Contract**.
Resolve `browser_ui_migration` without switching the production default during the design step.
Define explicit routing, user-visible mode selection, rollback behavior, and preservation of specialized Rinka Reference / Color Strip modes.
Do not mark the performance budget ready until a representative latency/resource budget is explicitly defined and evaluated.
