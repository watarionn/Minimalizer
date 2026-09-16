# Minimalizer 2.0 Calibration 05 Phase T

## Purpose

Phase T closes the final migration blocker: `performance_budget`.
It defines a versioned default-migration performance budget before the final hosted-envelope measurement, evaluates the current V2 implementation against it, and regenerates migration readiness.

This phase does **not** switch the browser default, merge to `main`, or deploy anything.
`ready_for_default=true` means the migration gate is clear, not that cutover has happened.

## Fixed budget

Schema: `minimalizer-v2-performance-budget-v1`.
Representative contract:
- canonical five-case service-level corpus;
- two repeats per case;
- legacy Standard level 4 PNG;
- V2 Minimal PNG with facets;
- sequential same-process timing with GC before each timed call.

Latency thresholds were fixed before the final 400-cap measurement:
- mean V2 <= `5.0 s`;
- slowest case mean V2 <= `5.5 s`;
- mean V2/legacy case ratio <= `7.0x`;
- maximum V2/legacy case ratio <= `9.0x`.

## Hosted resource envelope

While validating Phase T, the canonical V2 preprocessing default was confirmed to be `768`, while the recorded Railway 1 GB production safety setting is `WEB_MAX_ANALYSIS_SIDE=400`.
The budget therefore uses the documented hosted envelope rather than silently assuming the larger V2 default:
- analysis max side <= `400`;
- `WEB_WORKERS=1`;
- `WEB_MAX_CONCURRENT_JOBS=2`.

No latency threshold was relaxed after this correction.
V2 keeps its canonical default of `768` outside the hosted migration path.
`PipelineConfig.analysis_max_side` and `web.service.minimalize_v2_path(..., analysis_max_side_cap=...)` were added so a future Standard migration route can explicitly apply the hosted cap without changing existing opt-in V2 defaults or deterministic PNG behavior.

## Final measurement

Formal artifact: `MINIMALIZER_2_CALIBRATION_05_PHASE_T_PERFORMANCE.json`.

Five-case/two-repeat results under the `400 / 1 worker / 2 slots` envelope:
- mean legacy: `0.739380 s`;
- mean V2: `4.383244 s`;
- slowest V2 case mean: `4.626395 s`;
- mean case ratio: `6.098657x`;
- maximum case ratio: `7.485155x`.

All nine latency/resource checks passed.
No resource increase is required by this migration budget.

## Migration readiness

Formal artifact: `MINIMALIZER_2_CALIBRATION_05_PHASE_T_READINESS.json`.

After the successful budget evaluation:
- `ready_for_default=true`;
- blocker count: `0`;
- blocker IDs: `[]`.

All previously blocked compatibility areas are now covered by explicit contracts from Phases P through S, and Phase T closes the remaining operations blocker.
Specialized modes remain intentionally out of scope for the Standard-engine migration and continue to use legacy routing.

## Safety and invariants

Phase T does not change the current browser routing state: `legacy_default` remains active.
It does not change `/api/v2/minimalize` behavior or its existing deterministic PNG contract.
The analysis cap is injectable only when explicitly supplied; canonical V2 continues to use the existing default when no cap is provided.
No GitHub Actions, PR, merge, `main` update, or deployment is part of this phase.

## Validation

Focused performance-budget, migration, and Web API tests: `37 passed, 1 warning`.
V2 full regression: `151 passed`.
Full repository regression: `487 passed, 2 failed, 1 warning`.
The two failures are the unchanged missing `tests/assets/false_face_phase85.png` failures; no new regression was observed.

## Next engineering step

After Phase T closure, proceed to Phase U: Default-Migration Dry Run / Release Candidate Verification.
Phase U should exercise the already-defined browser rollout contract in a non-default, reversible path and validate the complete migration route before any explicit cutover decision.
It must not silently change the production browser default.
