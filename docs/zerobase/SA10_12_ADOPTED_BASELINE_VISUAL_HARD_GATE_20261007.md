# SA10.12 Adopted Baseline Binding & Visual Hard-Gate Backfill — 2026-10-07

Status: COMPLETE / BASELINE BINDING LEGITIMIZED / FEATURE SURVIVAL BACKFILLED / FACE HARD FAIL EXPOSED

## Goal

Create a legitimate adopted-baseline protocol for non-GC001 cases, then backfill Feature Survival and forbidden-face-detail evidence without candidate self-reference.

## Baseline adoption contract

Added:
- `minimalizer_zerobase/evaluation/adopted_baseline_registry.py`
- `tools/run_sa1012_visual_hard_gate.py`

An adoption record requires:
- case ID;
- source SHA-256;
- adopted baseline artifact SHA-256;
- baseline origin;
- stable baseline artifact ID;
- explicit `ADOPTED` review status;
- reviewer;
- non-empty review evidence;
- adoption transaction ID;
- immutable record flag;
- evaluation-baseline permission;
- production-inference prohibition;
- candidate-self-reference prohibition.

The evaluation transaction must differ from the adoption transaction.

Byte-identical fresh output is allowed only when it is generated in a later, separate evaluation transaction. Same-transaction self-reference fails closed.

## Adopted baselines

### Hyakuto-Kyoko

Adoption record:
`benchmarks/regression/sa10/baselines/Hyakuto-Kyoko.sa10.12-adoption.json`

Source SHA:
`cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`

Adopted SA10.11 baseline SHA:
`294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b`

Drive artifact ID:
`1DEIloGhLYw3-iVSpCnEa1wd1Uep9Yi4-`

Adoption transaction:
`sa10.12-adopt-hyakuto-kyoko-20261007-v1`

Evaluation transaction:
`sa10.12-eval-hyakuto-kyoko-20261007-v1`

### Juufuutei-Raden_stylecal_source

Adoption record:
`benchmarks/regression/sa10/baselines/Juufuutei-Raden_stylecal_source.sa10.12-adoption.json`

Source SHA:
`64022608d65006e7984a556c7140a3880a76b434e42b4ec9b3f48441dfeb87e3`

Adopted SA10.11 baseline SHA:
`a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f`

Drive artifact ID:
`1xfuLMuLjGLFEieug_pRFL8zJMxdtekoD`

Adoption transaction:
`sa10.12-adopt-juufuutei-raden-20261007-v1`

Evaluation transaction:
`sa10.12-eval-juufuutei-raden-20261007-v1`

## Fresh candidate regeneration

Both cases were regenerated after the adoption records already existed.

Fresh Phase12 candidate hashes:
- Kyoko: `294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b`
- Raden: `a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f`

Both are byte-identical to their adopted baselines, but the binding reports confirm:
- adoption transaction != evaluation transaction;
- same_transaction = false;
- candidate_self_reference_forbidden = true;
- production_inference_allowed = false.

## Unicode-safe baseline loading

The canonical Google Drive path contains Japanese characters. Windows OpenCV `imread` failed on that path even though the file existed and its SHA could be read.

The SA10.12 runner now uses:
- `numpy.fromfile`
- `cv2.imdecode`

This avoids path-codepage corruption and safely reads the existing Japanese Drive path without creating a new path.

## Fresh visual hard gate

Canonical gate:
`sa7.35-v2`

### Hyakuto-Kyoko

Feature Survival:
- AVAILABLE
- PASS
- required signatures: 17
- missing: 0

Forbidden Face Detail:
- AVAILABLE
- FAIL
- ratio: 0.058444259567387684
- maximum allowed: 0.0

Canonical visual hard gate:
- FAIL

### Juufuutei-Raden_stylecal_source

Feature Survival:
- AVAILABLE
- PASS
- required signatures: 9
- missing: 0

Forbidden Face Detail:
- AVAILABLE
- FAIL
- ratio: 0.012738853503184714
- maximum allowed: 0.0

Canonical visual hard gate:
- FAIL

The face failures are not hidden, averaged away, or overridden by Phase14 or DINO.

## Other hard evidence

Fresh candidate transaction:
- Source Authority: PASS / PASS
- Anatomy: PASS / PASS
- Topology: PASS / PASS
- Phase14 machine: PASS / PASS
- Phase14 human visual: PASS / PASS
- determinism: PASS / PASS

Fresh Phase14 deterministic-evaluation SHA:
- Kyoko: `b52efcf059a4a14e76e3961b113696baba7c26b7286defd0ea296076bad0f738`
- Raden: `109beb549baa132d006da900e0ea90fe3e2a99fa86e72b7b99abbaa1212d0d55`

SA9 Teacher evidence remains UNAVAILABLE for both cases.

## Preserved evidence

Per case:
- adoption record;
- Feature Survival report;
- forbidden-face-detail report;
- combined SA10.12 hard-evidence report;
- SA10.12 regression fixture.

Cross-case:
`benchmarks/regression/sa10/SA10_12_cross_case_matrix.json`

Matrix SHA-256:
`5746b77d68e2ceb60920415129c145fcbdd7c8f65c566e110df0394a0e785305`

## Verification

Focused chain:
- 29/29 PASS

Covered:
- adopted-baseline contract;
- same-transaction rejection;
- exact source/baseline SHA binding;
- Unicode-safe visual-hard-gate runner dependencies;
- canonical hard gate;
- SA10.11 structural hard evidence;
- SA10.12 Feature Survival / forbidden-face evidence;
- cross-case matrix visibility.

## Boundaries preserved

- Golden is not a production inference input;
- browser fallback is not a production inference input;
- adopted baseline is evaluation-only;
- no candidate is adopted in the same evaluation transaction;
- no hard failure is overridden by semantic/DINO diagnostics;
- no aggregate quality score;
- no new production threshold;
- no generative img2img / fill / inpainting.

## Decision

SA10.12 is complete.

The missing visual hard-gate evidence has been legitimately backfilled. The only newly exposed visual hard failure in the two non-GC001 cases is forbidden face detail. SA10.13 should repair face neutralization at the production-candidate level, then rerun the same baseline-bound hard gate.


## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_12_20261007_BASELINE_VISUAL_HARD_GATE`

Drive folder ID:
`1zo_nTfgcPMbd0CEKjl1yjwDKszrOA1GG`

The folder was created through the Drive API under the existing canonical Semantic_Abstraction parent. No new Japanese parent path was created through the local mount.

Drive API read-back verified all 15 preserved artifacts:
- 2 adoption records;
- 2 Feature Survival reports;
- 2 forbidden-face-detail reports;
- 2 combined hard-evidence reports;
- 2 SA10.12 fixtures;
- 2 fresh Phase12 final PNGs;
- 2 fresh Phase14 evaluation JSONs;
- 1 cross-case matrix.
