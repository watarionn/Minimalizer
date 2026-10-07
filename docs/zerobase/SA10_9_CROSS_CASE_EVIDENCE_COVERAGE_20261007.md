# SA10.9 Cross-Case Evidence Coverage — 2026-10-07

Status: COMPLETE / EXACT-OUTPUT DINO EVIDENCE / RADEN DROP ROOT CAUSE RESOLVED / NO THRESHOLDS

SA10.9 increases non-GC001 evidence coverage without converting missing evidence into proxy values.

## Implemented

### Macro alignment root-cause diagnostic

Added:
`minimalizer_zerobase/evaluation/macro_geometry_alignment_diagnostic.py`

The diagnostic distinguishes:
- `ALIGNED`
- `BUDGET_MASS_GAP`
- `PRIMITIVE_GENERATION_DROP`

It also records the concrete primitive rejection reason and fallback expansion / source-coverage values.

Raden result:
- hair budget: 1
- hair major components: 1
- hair mass candidates: 1
- hair emitted primitives: 0
- status: `PRIMITIVE_GENERATION_DROP`
- rejection: `EXPANSION_EXCEEDED`
- fallback expansion: 1.2861805086653162
- safety maximum: 1.12
- fallback source coverage: 0.9401305424262886
- minimum source coverage: 0.65

Therefore the SA10.8 mismatch was not a budget/report mismatch and not missing source support. The allocated hair mass is source-supported, but coarse polygon generation expands it too far and correctly fails closed.

major_clothing remains aligned:
- budget 1
- mass candidate 1
- emitted primitive 1

### Hash-bound exact-output DINO runner

Added:
`research/differentiable_minimalization/run_sa10_exact_semantic_retention.py`

The runner requires:
- exact source SHA-256
- exact candidate SHA-256
- frozen local DINOv3 model
- no production write
- no hard-gate override

Model:
`facebook/dinov3-convnext-tiny-pretrain-lvd1689m`

The output is a normal SA7.45 `SemanticRetentionReport`, plus DINO spatial research diagnostics.

## Exact Phase14 semantic-retention evidence

### Hyakuto-Kyoko

Source SHA:
`cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`

Final Phase14 output SHA:
`ef3dd1b21c6a3b671ffd7f74523c66016fac1d35b6fd2c4b35d1d33b4767c6c3`

SA7.45:
- global similarity: 0.7611358686048268
- patch similarity: 0.697618564473334
- semantic retention: 0.7293772165390804
- status: AVAILABLE
- authoritative: false
- can_override_hard_fail: false

Research-only DINO spatial score:
- 0.4016430028739799

Evidence artifact SHA-256:
`f061aaa7f47135e1a8ab1a90bca3179f830c1148be586c0e05369238a72d52b2`

### Juufuutei-Raden_stylecal_source

Source SHA:
`64022608d65006e7984a556c7140a3880a76b434e42b4ec9b3f48441dfeb87e3`

Final Phase14 output SHA:
`db655f3cf1b2acac603e7855bcbefd1a92c6f95225ddca69fd21d923f1f8bb42`

SA7.45:
- global similarity: 0.8725163181780999
- patch similarity: 0.7594218660520907
- semantic retention: 0.8159690921150953
- status: AVAILABLE
- authoritative: false
- can_override_hard_fail: false

Research-only DINO spatial score:
- 0.5577777938009946

Evidence artifact SHA-256:
`5eec1e15cd81983f00e71a0ec63eea0116c4279e073c374537b3e69855368f82`

The hash-bound runner regenerated both artifacts byte-for-byte with matching SHA-256.

## SA10.9 cross-case coverage

Hyakuto-Kyoko:
- semantic retention: 0.7293772165390804
- adaptive complexity: 0.8
- component survival: 0.5714285714285714
- primitive economy: 1.0
- teacher coverage: UNAVAILABLE
- teacher disagreement: UNAVAILABLE

Juufuutei-Raden_stylecal_source:
- semantic retention: 0.8159690921150953
- adaptive complexity: 0.4
- component survival: UNAVAILABLE
- primitive economy: UNAVAILABLE
- teacher coverage: UNAVAILABLE
- teacher disagreement: UNAVAILABLE

Raden component/economy remain unavailable intentionally. The primitive drop is now explained, but SA10.5 requires budget/emission frame alignment; SA10.9 does not silently change that metric contract.

## Hard evidence

For both non-GC001 cases:
- Phase14 machine: PASS
- Phase14 human visual: PASS
- determinism: PASS

Still individually UNAVAILABLE:
- Feature Survival hard report
- forbidden-face-detail hard report
- anatomy hard report
- topology hard report
- source-authority hard report

Phase14 metrics are not renamed into these hard categories.

## Reproducible matrix

Generated:
`benchmarks/regression/sa10/SA10_9_cross_case_matrix.json`

SHA-256:
`b3f9ec85fb6772c8377afec139b7037d25f000d7a168a5cdbe75b9129f181363`

Coverage:
- semantic retention: 2/2 AVAILABLE
- adaptive complexity: 2/2 AVAILABLE
- component survival: 1/2 AVAILABLE
- primitive economy: 1/2 AVAILABLE
- teacher coverage: 0/2 AVAILABLE
- teacher primitive disagreements: 0/2 AVAILABLE

No aggregate quality score and no calibration threshold were added.

## Verification

Focused chain:
- 18/18 PASS

The chain covers:
- SA10.9 macro alignment diagnostic
- SA10.9 evidence binding
- SA10.8 cross-case matrix
- SA10.5 component support
- SA10.4 component/economy evidence

## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_9_20261007_CROSS_CASE_EVIDENCE`

Drive folder ID:
`1QnLt0T5AvCOXk8BO0iaH0d_QxCNZhdLH`

Drive API readback verified:
- `Hyakuto-Kyoko.sa10.9-semantic-retention.json`
- `Juufuutei-Raden_stylecal_source.sa10.9-semantic-retention.json`
- `Juufuutei-Raden_stylecal_source.sa10.9-macro-alignment.json`
- `SA10_9_cross_case_matrix.json`

## Decision

SA10.9 is complete.

The next problem is not threshold calibration. The remaining work is to backfill explicit non-GC001 hard evidence and decide how an actual-emission component/economy diagnostic should coexist with the existing budget-aligned SA10.5 contract.
