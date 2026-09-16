# Minimalizer 2.0 Calibration 05 Phase O

## Purpose

Phase O reassesses performance and default-migration readiness after the exact-result optimization sequence through Phase N.
It is an observational and decision phase only: no image-producing algorithm, public default, route, or compatibility behavior is changed.

The goals are:
- compare current V2 service-level latency with the Phase I migration evidence;
- regenerate the migration-readiness gate from the current implementation;
- decide whether performance or compatibility should drive the next engineering phase.

## Performance reassessment

The Phase I five-case service-level comparison reported mean legacy `0.740 s`, mean V2 `5.954 s`, and mean per-case ratio `8.28x`.
Phase O reran the same canonical five cases through legacy PNG and V2 PNG file boundaries with two repeats per case.
| Case | Phase O legacy s | Phase O V2 s | V2 / legacy |
| --- | ---: | ---: | ---: |
| Kikirara-Vivi | 0.728 | 4.826 | 6.63x |
| Otonose-Kanade | 0.575 | 4.478 | 7.79x |
| Todoroki-Hajime | 0.604 | 3.890 | 6.44x |
| Raora-Panthera | 0.883 | 4.615 | 5.23x |
| Hakos-Baelz | 0.894 | 4.448 | 4.97x |

Phase O means:
- legacy: `0.736762 s`
- V2: `4.451426 s`
- mean per-case ratio: `6.2129x`

Relative to Phase I evidence, legacy is essentially unchanged (`-0.44%`) while V2 mean latency is about `25.24%` lower.
The mean V2/legacy ratio is about `24.97%` lower than the Phase I `8.28x` evidence.

Canonical service-level artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_O_PERFORMANCE.json`.
## Migration-readiness reassessment

The current machine-readable readiness report still returns:
- `ready_for_default=false`
- blocker count: `6`
- blockers: `web_control_mapping`, `output_format_parity`, `alpha_background_parity`, `cli_control_mapping`, `browser_ui_migration`, `performance_budget`

Ready areas remain unchanged:
- canonical quality
- deterministic PNG export
- opt-in entry-point boundary

The performance evidence is substantially better, but `performance_budget` remains blocked because no default-migration latency/resource budget has been approved.
Phase O deliberately does not invent an SLA or convert improved measurements into a readiness pass.

Canonical readiness snapshot:
`MINIMALIZER_2_CALIBRATION_05_PHASE_O_READINESS.json`.

Focused migration tests: `3 passed`.
Phase N regression remains the current image-producing baseline: V2 `134 passed`; full repository `470 passed, 2 failed, 1 warning` with only the known missing `tests/assets/false_face_phase85.png` failures.
## Decision

Performance is no longer the only obvious migration risk, but it is not yet a closed blocker.
The next work should shift from blind optimization to explicit public-contract compatibility work.

## Next engineering step

Proceed to Phase P: Public Contract Compatibility Mapping.
Build a machine-readable matrix for the legacy standard Web and CLI controls and classify every public control as:
- directly mapped to V2;
- retained on the legacy route during migration;
- intentionally deprecated through a versioned decision;
- out of scope for the standard-engine migration.

Phase P must not switch defaults or change browser routing.
It should establish the contract needed to address `web_control_mapping` and `cli_control_mapping`, and expose dependencies on output-format and alpha/background parity before implementation begins.
