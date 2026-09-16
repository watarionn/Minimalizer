# Minimalizer 2.0 Calibration 05 Phase Q

## Purpose

Phase Q resolves the `output_format_parity` migration blocker without inventing unsupported V2 formats.
The goal is backward-compatible routing, not forcing every legacy output format through V2.

No image-generation algorithm, visual threshold, preset, browser default, alpha/background behavior, or deployment state changes in this phase.

## Decision

Adopt a versioned output-format compatibility contract:

- Web PNG -> V2-capable route after default migration
- Web SVG -> legacy renderer retained
- CLI PNG -> V2-capable route after default migration
- CLI SVG -> legacy renderer retained
- CLI WEBP -> legacy renderer retained

The current defaults remain unchanged until a later migration phase explicitly changes routing.

## Why routing instead of V2 SVG / WEBP

Phase I explicitly allowed either native V2 format contracts or a backward-compatible routing policy.
V2 currently has a stable deterministic PNG contract, while legacy SVG has vector semantics and legacy WEBP has established behavior.

Claiming new V2 SVG/WEBP contracts merely to remove a blocker would risk changing semantics without user benefit.
The routing contract therefore preserves those mature legacy renderers and uses V2 only where its export contract is already proven.

## Machine-readable contract

Schema: `minimalizer-v2-output-format-v1`.

Canonical artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_Q_OUTPUT_FORMAT.json`.

Generator:
`tools/report_v2_output_format_compatibility.py`.

The contract is covered by drift tests against the actual Web and CLI public surfaces.

## Readiness result

`output_format_parity` is now ready because every currently exposed standard output format has an explicit backward-compatible route.

Migration readiness changes from four blockers to three:
- `alpha_background_parity`
- `browser_ui_migration`
- `performance_budget`

`ready_for_default` remains `false`.

Canonical readiness artifact:
`MINIMALIZER_2_CALIBRATION_05_PHASE_Q_READINESS.json`.

## Validation

Focused output-contract + migration tests: `5 passed`.
V2 regression: `139 passed`.
Full repository: `475 passed, 2 failed, 1 warning`.

The two failures remain the pre-existing missing `tests/assets/false_face_phase85.png` failures.
No rendering code changed, so the Phase N exact-output evidence remains the latest canonical image-equivalence proof.

## Next engineering step

Proceed to Phase R: Alpha / Background Compatibility Contract.

Resolve `alpha_background_parity` with the same discipline:
- preserve established legacy source/white/transparent/custom behavior;
- do not silently composite away source alpha;
- do not change V2 visual thresholds or canonical RGB behavior for opaque inputs;
- keep browser default routing unchanged;
- leave the performance-budget blocker untouched unless separately approved.
