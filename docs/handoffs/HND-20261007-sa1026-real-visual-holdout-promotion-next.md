# Handoff — SA10.26 Real Visual Gate and Holdout Promotion

Start from the closed SA10.25 material-topology implementation.

Required before production promotion:

1. Independently review real GC001 source versus SA10.25 clean4 output for silhouette, face/head shape, visible arms, pose, color masses, and identity-bearing features.
2. Rerun the established SA10 PASS transactions without weakening any gate.
3. Run one untouched fresh holdout. Do not use it for threshold calibration.
4. Preserve comparison/evidence artifacts under Google Drive `chatGPT及びCodex用` in the established Minimalizer hierarchy.
5. If machine and human gates pass, push/merge and perform production deployment plus rollback verification. Otherwise keep production unchanged and record the exact blocker.

Hard invariants: fragmentation <= 0.20; source boundary >= 0.90; source topology, anatomy, provenance, semantic relations remain hard; no generated visible content or case-specific repair.
