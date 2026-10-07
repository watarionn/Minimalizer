# SA10.8 Cross-Case Regression Expansion — 2026-10-07

Status: COMPLETE / CROSS-CASE MATRIX / PARTIAL DIAGNOSTIC COVERAGE

SA10.8 expands the regression envelope beyond GC001 using two existing canonical non-GC001 production chains:

1. Hyakuto-Kyoko
2. Juufuutei-Raden_stylecal_source

Both have source role-mask artifacts and deterministic Phase14 production evaluation outputs.

## New implementation

`minimalizer_zerobase/evaluation/cross_case_regression_matrix.py`

Contract version:
`sa10.8-v1`

The matrix:
- requires at least two unique cases;
- exposes exactly the six SA10 diagnostic names;
- preserves unavailable evidence with explicit reasons;
- keeps hard-evidence categories individually visible;
- computes only per-diagnostic available counts, min/max and case values;
- creates no aggregate quality score;
- creates no calibrated thresholds;
- derives no threshold from GC001.

## Case evidence

### Hyakuto-Kyoko

Source:
- 340x340
- SHA-256 `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`

Phase14:
- machine PASS
- human visual PASS
- determinism PASS
- evaluation SHA `169d1511cabbd55c36a748f8c9acfe7d144ed0d75566dbd7b21ee7a9bdf4c467`

Fresh SA10.8 role-mask remeasurement:
- adaptive complexity: 0.8
- component survival: 4/7 = 0.5714285714285714
- primitive economy: 1.0

Unavailable:
- semantic retention: preserved DINO evidence predates the final Phase14 31-primitive output
- teacher coverage/disagreement: no reviewed SA9 teacher annotation

Phase14 context metrics are retained only as context, not silently mapped into SA10:
- silhouette: 0.981039
- identity retention: 0.963008
- Phase14 primitive economy: 0.8037974683544304

### Juufuutei-Raden_stylecal_source

Source:
- 512x512
- SHA-256 `64022608d65006e7984a556c7140a3880a76b434e42b4ec9b3f48441dfeb87e3`

Phase14:
- machine PASS
- human visual PASS
- determinism PASS
- evaluation SHA `2fb98dbbf1ff3dc316b81f2eda562e530b3ba5abdd6b50e2fe4041edf944c7d3`

SA10 diagnostics remain unavailable where the exact evidence contract is not satisfied.
A fresh SA10.8 component/economy attempt failed closed because emitted macro primitive count did not match the SA7.43 budget frame for hair. No proxy value is substituted.

Phase14 context only:
- silhouette: 0.984893
- identity retention: 0.975258
- Phase14 primitive economy: 0.46153846153846156

The older 340x340 Diagnostic-2 Raden DINO evidence is not mixed into this 512x512 source chain.

## Hard-evidence visibility

For both cases, Phase14 machine/human/determinism evidence is explicit.

The following SA10 hard categories remain individually visible as UNAVAILABLE rather than being inferred from Phase14:
- Feature Survival
- forbidden face detail
- anatomy
- topology
- source authority

Source SHA binding is provenance and is not silently promoted into the source-authority hard gate.

## Deterministic matrix

Canonical fixtures:
- `benchmarks/regression/sa10/Hyakuto-Kyoko.sa10.8.json`
- `benchmarks/regression/sa10/Juufuutei-Raden_stylecal_source.sa10.8.json`

Expected canonical matrix SHA-256:
`5b3d45884f8a4f83834b80cadd16009607786beb93733ee09ee48954022d727d`

## Interpretation

Cross-case expansion immediately shows why one-case threshold calibration would be unsafe:
- Kyoko supplies three compatible SA10 diagnostics.
- Raden exposes a measurement-contract gap instead of a value.
- semantic teacher evidence is absent for both non-GC001 cases.

The correct next step is evidence coverage expansion, not threshold promotion.
