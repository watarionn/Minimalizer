# SA10.2 Regression Diagnostic Adapters — 2026-10-07

Status: COMPLETE / DETERMINISTIC ADAPTERS / NO THRESHOLDS

Added `evaluation/regression_diagnostic_adapters.py`.

Adapters now connect existing evidence to the SA10 envelope:
- SemanticRetentionReport -> semantic_retention_score
- AdaptivePrimitiveBudget -> allocated_total / global_cap
- explicit ComponentSurvivalEvidence -> surviving / source components
- explicit PrimitiveEconomyEvidence -> supported / emitted primitives
- TeacherCoverageDiagnostic -> coverage ratio + primitive disagreement count

Rules:
- absent evidence stays UNAVAILABLE;
- semantic and teacher observer authority violations fail closed;
- component and primitive evidence cannot claim authority;
- adaptive complexity is utilization, not quality;
- no thresholds or aggregate quality score were introduced;
- diagnostics still cannot rescue or fail the canonical hard gate.

Verification: 35/35 focused and related tests PASS.

Next: SA10.3 should assemble a reproducible GC001 regression diagnostic artifact using only evidence that actually exists. Missing component/economy evidence must remain UNAVAILABLE rather than synthesized.
