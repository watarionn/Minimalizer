# Minimalizer 2.0 Calibration 05 Phase P

## Purpose

Phase P resolves ambiguity in the public migration contract without changing the image-producing pipeline.
It classifies every exposed legacy standard Web and CLI control before any default-route migration.

The allowed dispositions are:
- `mapped`: exact public-boundary equivalence exists now
- `legacy_retained`: legacy semantics stay on the legacy route until a later compatibility phase resolves them
- `versioned_deprecated`: removal is allowed only by an explicit versioned decision
- `out_of_scope`: specialized modes remain separately routed

No control is treated as equivalent merely because a V2 concept looks similar.
No legacy control is deprecated in this phase.

## Machine-readable contract

Schema: `minimalizer-v2-public-contract-v1`.
Builder: `build_public_contract_compatibility()`.
Generator: `tools/report_v2_public_contract_compatibility.py`.
Canonical snapshot: `MINIMALIZER_2_CALIBRATION_05_PHASE_P_COMPATIBILITY.json`.

The matrix contains `66` controls in total:
- mapped: `2`
- legacy-retained: `58`
- versioned-deprecated: `0`
- out-of-scope: `6`

## Web contract decision

The current legacy Web endpoint surface is inspected directly from `web.app.minimalize_image`.
The compatibility matrix covers every exposed argument except the framework-internal `request` object.

Decisions:
- source `file` is mapped to the same V2 source-image boundary
- `level`, `output_format`, `mode`, `colors`, `max_shapes`, and `background` are legacy-retained
- Color Strip controls and `rinka_preset` are out of scope and stay on specialized legacy routes

The retained controls are not silently translated to a V2 preset or stage configuration.
Such a translation would require an explicit semantic contract in a later phase.

## CLI contract decision

The matrix covers all `53` legacy CLI controls returned by `build_parser()` after excluding help and the three V2-only shadow controls.

Decisions:
- positional `input` is mapped to the V2 source-image path
- the remaining `52` controls are legacy-retained
- no legacy CLI control is deprecated

This includes output format/path controls, level/detail controls, alpha/background controls, composition/cleanup controls, character/face/hand controls, quality/debug controls, and preset-specific legacy behavior.

## Migration-readiness effect

Phase P changes only the classification state of two readiness items:
- `web_control_mapping`: `blocked -> ready`
- `cli_control_mapping`: `blocked -> ready`

The default migration is still not ready.
The canonical Phase P readiness snapshot reports `4` blockers:
- `output_format_parity`
- `alpha_background_parity`
- `browser_ui_migration`
- `performance_budget`

Snapshot: `MINIMALIZER_2_CALIBRATION_05_PHASE_P_READINESS.json`.

Legacy-retained controls do not imply parity. They explicitly preserve old behavior while the dependent blocker remains open.
This phase therefore reduces contract ambiguity without weakening compatibility requirements.

## Validation

Focused compatibility + migration tests: `6 passed`.
V2 regression: `137 passed`.
Full repository regression: `473 passed, 2 failed, 1 warning`.

The two failures remain the pre-existing missing `tests/assets/false_face_phase85.png` failures.
Phase P changes no segmentation, hierarchy, contour, primitive, palette, detail-budget, facet, render, or export computation.
Phase N exact-output evidence therefore remains the current image-producing baseline.

## Decision

Adopt the Phase P public-contract compatibility matrix as the canonical migration classification.
Do not invent one-to-one mappings for legacy controls whose semantics are not equivalent to V2.
Do not remove or deprecate a retained control without a later explicit versioned decision.

## Next engineering step

Proceed to **Calibration 05 Phase Q: Output Format Compatibility Contract**.

Resolve `output_format_parity` next because both Web and CLI retain legacy output behavior today.
Phase Q should determine and implement the smallest backward-compatible policy for legacy SVG/PNG/WEBP expectations while preserving the deterministic V2 PNG contract.
Do not change browser default routing, alpha/background semantics, or performance-budget status as part of that step unless independently proven and documented.
