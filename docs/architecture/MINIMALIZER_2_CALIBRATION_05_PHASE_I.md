# Minimalizer 2.0 Calibration 05 Phase I

## Legacy-to-V2 Migration Readiness

Date: 2026-09-16
Scope: determine whether the legacy **standard** default can safely move to V2.
This phase does not switch defaults, alter the browser UI, merge, or deploy.
Rinka Reference and Color Strip remain separate specialized modes and are out of scope.

## Result

Default migration is **not ready**.
The machine-readable gate reports `6` blockers and `ready_for_default=false`.
This is not a new visual-quality failure: canonical V2 quality, deterministic PNG export,
and the opt-in Web/CLI boundary are already ready.

Canonical machine-readable snapshot:
`docs/architecture/MINIMALIZER_2_CALIBRATION_05_PHASE_I_READINESS.json`

Generator:
`tools/report_v2_migration_readiness.py`

Schema:
`minimalizer-v2-migration-v1`
## Ready areas

The readiness gate marks these areas ready:

1. `canonical_quality`
   - Phase H canonical 18-case hard invariant failures: `0 / 18`.
2. `deterministic_png`
   - V2 export contract `minimalizer-v2-png-v1` is byte deterministic and hash-addressable.
3. `entry_point_boundary`
   - Phase H opt-in Web and CLI paths preserve Phase G V2 bytes without changing legacy defaults.

These areas do not need to be reopened merely to migrate the standard entry point.

## Migration blockers

The current six blockers are:

1. `web_control_mapping`
   - legacy standard: `level`, `colors`, `max_shapes`, `background`, SVG/PNG
   - V2 opt-in: `preset`, `include_facets`, PNG only
2. `output_format_parity`
   - legacy Web: SVG/PNG
   - legacy CLI: SVG + optional PNG/WEBP
   - V2: PNG only
3. `alpha_background_parity`
   - legacy supports source/white/transparent/custom background semantics and alpha controls
   - V2 file input currently composites alpha onto white RGB
4. `cli_control_mapping`
   - legacy CLI exposes many detail/composition/cleanup/character/face/hand/debug controls
   - V2 CLI currently exposes only shadow PNG, preset, and facet opt-out
5. `browser_ui_migration`
   - browser UI intentionally continues to submit only legacy modes
   - V2 remains API-only opt-in
6. `performance_budget`
   - no migration latency/resource threshold has yet been approved
   - current smoke evidence shows a substantial runtime gap

A future migration gate passes only when every item marked `blocked` is either
implemented compatibly or deliberately removed from the default contract through an explicit versioned decision.

## Entry-point surface evidence

Current exposed surfaces were inspected from the implementation, not inferred from documentation.
`MinimalizeConfig` contains `219` legacy configuration fields.
V2 `PipelineConfig` contains seven stage configs with `180` nested fields.
The migration gate intentionally compares public behavior rather than demanding one-to-one mapping of all internal fields.
## Performance smoke evidence

Five canonical cases were measured through the same Web-service-level file boundary.
Legacy used standard level 4 with hosted analysis cap `640`; V2 used preset `minimal`.
This is observational evidence, not an approved latency threshold.

| Case | Legacy s | V2 s | V2 / legacy |
| --- | ---: | ---: | ---: |
| Kikirara-Vivi | 0.726 | 6.364 | 8.77x |
| Otonose-Kanade | 0.605 | 6.190 | 10.23x |
| Todoroki-Hajime | 0.608 | 5.561 | 9.15x |
| Raora-Panthera | 0.871 | 6.338 | 7.28x |
| Hakos-Baelz | 0.889 | 5.314 | 5.97x |

Mean legacy time: `0.740 s`.
Mean V2 time: `5.954 s`.
Mean per-case ratio: `8.28x`.

The benchmark therefore confirms that performance is a concrete blocker rather than merely missing documentation.
Do not treat these five measurements as a production SLA; Phase J should profile the V2 stage timings before choosing any budget.
## Validation

Focused migration/Web/CLI/export tests: `38 passed, 1 warning`.
V2 full regression: `128 passed`.
Full repository regression: `464 passed, 2 failed, 1 warning`.
The two failures are the pre-existing missing `tests/assets/false_face_phase85.png` failures.
The warning is the existing Starlette TestClient deprecation warning.
No legacy default route or browser UI behavior was changed by Phase I.

Phase I adds only:
- a first-class migration-readiness data model and gate
- a reproducible JSON report tool
- a canonical readiness JSON snapshot
- tests that bind the report assumptions to the actual Web/CLI surfaces
- this decision record

## Next engineering step

Proceed to **Calibration 05 Phase J: V2 Performance Profiling / Budget Preparation**.

Profile the V2 phase timings on the representative corpus, identify the dominant runtime stages,
and test conservative optimizations that do not alter canonical pixels, algorithm digest, hierarchy,
or accepted facet behavior. Do not invent a migration SLA and do not change the legacy default.
After performance is understood, return to the remaining compatibility blockers with evidence rather than guesswork.
