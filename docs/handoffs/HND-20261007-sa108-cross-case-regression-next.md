# Handoff — SA10.8 Cross-Case Regression Expansion — 2026-10-07

Status: SA10.7 COMPLETE / SA10.8 NEXT

Goal:
Expand the complete SA10 diagnostic envelope beyond GC001 without calibrating thresholds from one case.

Requirements:
1. select at least two existing canonical non-GC001 cases with source role masks and deterministic production outputs;
2. generate the same six diagnostics where evidence exists;
3. preserve UNAVAILABLE when a case genuinely lacks evidence;
4. compare metric distributions across cases without aggregate scoring;
5. keep Feature Survival / face / anatomy / topology / source-authority hard failures individually visible;
6. do not derive production thresholds from GC001;
7. record per-case provenance and deterministic hashes;
8. prepare a cross-case matrix suitable for later calibration work.

GC001 reference panel:
- semantic retention 0.7298672763136121
- adaptive complexity 0.8
- component survival 0.4444444444444444
- primitive economy 1.0
- teacher coverage 0.25
- teacher primitive disagreements 0
- hard gate PASS
