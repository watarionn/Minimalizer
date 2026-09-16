# Minimalizer 2.0 Calibration 05 Phase V

Status: pre-cutover gate passed locally on RDC.

## Purpose

Phase V is the final explicit cutover gate after the Phase U release-candidate dry run.
It verifies that a future `v2_standard_default` state preserves all compatibility routing
while production remains unchanged until the user explicitly approves cutover.

## Gate conditions

Phase U RC must be PASS and rollback-verified.
The current browser migration contract must still report `legacy_default`.
Eligible Standard PNG + white + opaque requests may route to V2 in the candidate state.
SVG and transparency-sensitive requests must remain legacy-routed.
`rinka_reference` and `color_strip` must remain legacy-routed.
Rollback must require no data migration and automatic error fallback remains disabled.

## Verification

Focused Phase V/U + browser/performance/Web suite: `45 passed, 1 warning`.
The first Phase V run exposed a test-construction error caused by duplicate keyword arguments;
the test was corrected without changing production code or migration behavior.
The corrected gate is fully green.

## Result

Phase V pre-cutover gate: PASS.
Production browser state remains `legacy_default`.
No PR, main change, merge, deployment, or default cutover has occurred.
