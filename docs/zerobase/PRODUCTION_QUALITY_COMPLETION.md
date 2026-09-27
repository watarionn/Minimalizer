# ZeroBase Production Quality Completion

Status: **CLOSED / MIGRATION GATE PASS**

## Structural fix

The Approved-78 canonical source PNGs contain an alpha channel. `SLICRegionAdapter` now supports an explicit `min_foreground_ratio` policy that uses this non-generative alpha evidence to exclude transparent/background regions before geometry production. Foreground filtering fails closed when alpha is absent instead of guessing a subject mask.

The migration corpus runner requires canonical alpha and uses `min_foreground_ratio=0.5`. A sweep over the first 18 canonical cases produced identical results from 0.05 through 0.75, demonstrating that the gain is driven by the source alpha boundary rather than a tuned threshold.

## Approved-78 full rerun

- source SHA-256: 78/78 verified
- reference SHA-256: 78/78 verified
- saved-Evidence replay: 78/78 deterministic
- ZeroBase mean silhouette IoU: 0.534959
- Minimalizer 2.0 mean silhouette IoU: 0.411292
- silhouette wins: ZeroBase 58 / Minimalizer 2.0 10
- ZeroBase mean foreground-ratio error: 0.162691
- Minimalizer 2.0 mean foreground-ratio error: 0.462800
- foreground-ratio wins: ZeroBase 48 / Minimalizer 2.0 20
- ZeroBase mean primitive count: 8.910256

## Final gate

`MigrationGate.switch_authorized = true` with no failure reasons.

Phase 12 FinalQualityGate also reports `foundation_ready=true`, `migration_ready=true`, and 78/78 replayable cases. ZeroBase tests: 67 passed. `git diff --check`: PASS.

This closes Production Quality Completion and establishes evidence-backed production-switch eligibility. Actual production routing remains a separate deployment action so the current Minimalizer 2.0 production boundary is not changed implicitly by a quality-calibration commit.
