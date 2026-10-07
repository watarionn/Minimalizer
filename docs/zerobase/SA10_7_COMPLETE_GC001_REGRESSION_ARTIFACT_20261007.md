# SA10.7 Complete GC001 Regression Artifact — 2026-10-07

Status: COMPLETE / ALL SIX DIAGNOSTICS AVAILABLE / HARD-GATE AUTHORITY PRESERVED

SA10.7 adds a deterministic complete GC001 regression artifact:
`minimalizer_zerobase/evaluation/gc001_complete_regression_artifact.py`

## Complete GC001 panel

- canonical hard gate: PASS
- semantic retention: 0.7298672763136121
- adaptive complexity: 0.8
- component survival: 0.4444444444444444
- primitive economy: 1.0
- teacher coverage: 0.25
- teacher primitive disagreements: 0

All six diagnostics are AVAILABLE.

## Authority boundary

- hard gate remains the only `pass_gate` authority;
- diagnostics cannot rescue a hard failure;
- no aggregate quality score is introduced;
- no new quality threshold is introduced;
- Golden evidence remains evaluation-only and cannot become production input.

## Canonical observer bundle compatibility

The historical SA7.45 artifact wraps reports as `baseline` and `candidate`.
SA10.7 explicitly consumes the candidate report only when:
- `production_output_changed=false`;
- `hard_gate_override_allowed=false`;
- candidate `authoritative=false`;
- candidate `can_override_hard_fail=false`.

This fixes the mismatch between the canonical stored observer bundle and the earlier normalized SA10 assembly input shape.

## Reproducible artifact

Generated:
`GC001_sa107_complete_regression.json`

SHA-256:
`c5f0709b2ee046942b55f68966d493c177f3395a4f82e8873e5a6e8d08660f54`

Companion evidence:
- `GC001_sa106_role_masks/`
- `GC001_sa106_component_economy.json`
- `GC001_sa9_teacher_evaluation.json`

## Verification

Focused SA9/SA10 chain:
- 35/35 PASS

The suite includes:
- SA10.7 complete artifact
- SA10.6 role-mask preservation
- SA10.5 component-to-primitive support
- SA10.4 component/economy evidence
- SA10.3 assembly
- SA10.2 adapters
- SA10.1 envelope
- SA9.4 teacher artifact
- SA9.3 teacher coverage

## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_20261007_REGRESSION_DIAGNOSTICS`

Drive folder ID:
`1-jV5ReW50t5T3p8IQiVS2IbOKQUlxSm1`

Drive API readback verified the complete artifact set:\n- `GC001_sa107_complete_regression.json`\n- `GC001_sa106_component_economy.json`\n- `GC001_sa9_teacher_evaluation.json`\n- `GC001_sa106_role_masks/` containing `hair.png`, `major_clothing.png`, and `manifest.json`.\n\nPreservation verification: PASS.

## Decision

GC001 is now the first complete SA10 regression reference case with a fully populated diagnostic panel and unchanged hard-gate authority.

No metric is promoted to a production threshold in this stage.
