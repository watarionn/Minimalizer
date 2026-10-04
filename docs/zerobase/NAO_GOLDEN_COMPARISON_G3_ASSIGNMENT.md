# Nao Assignment: Golden Comparison G3/G4 Bridge

/goal Make Feature Survival Gate generic, fail-closed, and impossible for perceptual evidence to override.

/plan
1. Review G3 Feature Survival Gate against the G2 semantic contract.
2. Challenge required/forbidden/unknown behavior with synthetic tests.
3. Keep observer confidence as evidence only; do not convert confidence into semantic truth.
4. Prepare G4 Semantic Feature Budgeter proposals that consume semantic importance without Case-001-specific production rules.
5. Continue VTracer and feature-local DINO PoCs only as isolated evidence experiments.
6. Report branch, commit SHA, exact tests, artifacts, and generalization risks for Rinka review.

Hard boundary:
- required absent or unknown = FAIL
- forbidden present or unknown = FAIL
- optional absence/unknown does not hard-fail
- perceptual score cannot compensate for any hard failure
- no Golden raster reconstruction input
