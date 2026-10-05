# Semantic Abstraction Baseline Freeze — 2026-10-05

Status: FROZEN
Scope: SA0 rollback/reproducibility record for the Semantic Abstraction Layer.

## Canonical references

- Development baseline `main`: `5164c77470d13468166fd60c15a588fafc82400d`
- Latest adopted visual baseline: `a60aaa12ff22c2f6384a598442964710ce939d87`
- Adopted visual stage: Silhouette Proportion Recomposition
- G9 first untuned blind artifact bundle SHA-256:
  `e446a04bcb913b354876048b40957f10d8a76126b5fb9aa4c76c111d15e72aab`
- G9 canonical record: `docs/zerobase/GOLDEN_G9_FIRST_BLIND_RUN.md`

The development baseline and visual rollback baseline are intentionally distinct. Documentation and
non-visual development may advance beyond the most recently adopted visual result.

## Frozen contracts

The existing G2-G9 Golden Comparison contracts remain authoritative constraints for this work.
The Semantic Abstraction Layer must not weaken:

- semantic feature survival,
- required feature reservation,
- semantic budget rules,
- sealed blind-corpus boundaries,
- face-detail prohibition,
- deterministic rendering and evaluation,
- Golden separation from the production reconstruction path.

## Rollback rule

If any behavior-changing semantic stage causes a hard regression, rollback is to the latest adopted
visual baseline `a60aaa12ff22c2f6384a598442964710ce939d87`, not merely to the newest documentation commit.

## Foundation verification

The SA1-SA4 foundation plus the policy-only face neutralization guard is production-output neutral.
At branch head `082fe558911c03a8d4474e4c594d68135949a862`:

- semantic-abstraction focused tests: 23 passed,
- full `tests/zerobase`: 496 passed,
- `git diff --check`: PASS.

No visual adoption is claimed by this record.
