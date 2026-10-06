# SA10.3 GC001 Regression Diagnostic Assembly — 2026-10-07

Status: COMPLETE / REPRODUCIBLE ASSEMBLY / PARTIAL DIAGNOSTICS

Implemented `evaluation/gc001_regression_assembly.py`.

Canonical GC001 evidence assembled:
- SA7.43 canonical hard gate: PASS, 16 required signatures, 0 missing, forbidden face detail 0
- SA7.43 adaptive macro budget: 4 / 5 allocated = 0.8 utilization
- SA7.45 DINOv3 semantic retention: 0.729867
- SA9 teacher coverage: 2 / 8 = 0.25
- SA9 primitive disagreement count: 0 comparable disagreements

Explicitly unavailable:
- component survival ratio
- primitive economy ratio

Those two metrics are not synthesized from nearby evidence. They remain UNAVAILABLE until explicit source/survival and supported/emitted counts exist.

Authority:
- canonical hard gate remains the only pass_gate authority
- diagnostics cannot rescue hard failure
- Golden data remains evaluation-only
- no aggregate quality score
- no new thresholds

Verification:
- SA10.3 + SA10.2 + SA10.1 focused suite: 17/17 PASS

Next: SA10.4 should create explicit component-survival and primitive-economy evidence contracts from source-supported geometry, then reassemble GC001 without inventing proxy counts.
