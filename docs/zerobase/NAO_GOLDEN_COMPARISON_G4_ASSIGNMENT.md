# Nao Assignment: Golden Comparison G4/G5 Bridge

/goal Challenge and generalize the Semantic Feature Budgeter, then prepare deterministic geometry re-authoring without Case-001 production heuristics.

/plan
1. Review G4 allocation ordering and fail-closed insufficient-budget behavior.
2. Add synthetic manifests that vary semantic roles, feature IDs, and list order to prove the budgeter is generic and deterministic.
3. Confirm forbidden/omit features never consume primitive budget.
4. Prepare G5 geometry grammar proposals for polygon, ellipse, ring, ribbon, trapezoid, and Bezier silhouette.
5. Keep VTracer limited to fitting already-authorized masks; it must not decide semantic ownership.
6. Report branch, commit SHA, exact tests, visual artifacts, and generalization risks for Rinka review.

Hard boundary:
- semantic importance and disposition may influence allocation
- pixel area alone must not determine priority
- Case-001 feature names/colors must not appear in production allocation logic
- insufficient budget must fail rather than silently delete required identity features
