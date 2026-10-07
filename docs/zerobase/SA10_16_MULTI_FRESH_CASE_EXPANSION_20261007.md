# SA10.16 Multi-Fresh-Case Expansion & Failure Taxonomy — 2026-10-07

Status: COMPLETE / FIVE REAL PASS TRANSACTIONS / FAILURE TAXONOMY ESTABLISHED / NO CALIBRATION

## Goal

Expand the SA10.14/15 regression-transaction protocol beyond three real cases, preserve every initial fresh-case failure, and classify failure modes before any threshold calibration.

## Fresh cohort

SA10.16 screened eight fresh cases:

- Fuwawa-Abyssgard
- La-Darknesss
- Nekomata-Okayu
- Kaela-Kovalskia
- Ouro-Kronii
- Shirakami-Fubuki
- Tokino-Sora
- Hoshimachi-Suisei

All source images were preserved under the canonical Google Drive `chatGPT及びCodex用` hierarchy before or during execution.

No SA10.16 case-specific production branch, coordinate, mask, color, or threshold was added.

## New admitted cases

### Nekomata-Okayu

Baseline adoption:
`sa10.16-adopt-nekomata-okayu-20261007-v1`

Fresh evaluation transaction:
`sa10.16-regression-nekomata-okayu-20261007-v1`

Hard evidence:
- Feature Survival: 14 required / 0 missing / PASS
- Forbidden Face Detail: 0.0 / PASS
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS
- Phase14 machine: PASS
- Phase14 human visual: PASS
- Determinism: PASS

DINO semantic retention:
`0.8200394367607636`

Phase14 determinism SHA:
`826b76e802a0dbd987f330687e0185049ccf6401bead332ebb2b22d5c075c0f5`

Transaction canonical payload SHA:
`c82d986fa343824bf88bda8822782295e8724f76f83194ed838803c987defbfa`

### Hoshimachi-Suisei

Baseline adoption:
`sa10.16-adopt-hoshimachi-suisei-20261007-v1`

Fresh evaluation transaction:
`sa10.16-regression-hoshimachi-suisei-20261007-v1`

Hard evidence:
- Feature Survival: 16 required / 0 missing / PASS
- Forbidden Face Detail: 0.0 / PASS
- Anatomy: PASS
- Topology: PASS
- Source Authority: PASS
- Phase14 machine: PASS
- Phase14 human visual: PASS
- Determinism: PASS

DINO semantic retention:
`0.825681250707786`

Phase14 determinism SHA:
`55e7c22c670a7d1925bc6cfa580ff61b008874a3af74502ca885a53ec6d9e793`

Transaction canonical payload SHA:
`a62e3d9d7d698721d2a27984287783ab4ab3ae951f8aa9eaf5b51b07680abf6b`

## Five-case real transaction set

Canonical:
`benchmarks/regression/sa10/SA10_16_transaction_set.json`

PASS cases:
1. AZKi
2. Hyakuto-Kyoko
3. Juufuutei-Raden_stylecal_source
4. Nekomata-Okayu
5. Hoshimachi-Suisei

Transaction count:
`5`

All five transactions:
`PASS`

The set contains no aggregate quality score. Every hard gate remains visible in its transaction artifact.

## Fresh failures preserved

Canonical taxonomy:
`benchmarks/regression/sa10/SA10_16_failure_taxonomy.json`

### Fuwawa-Abyssgard

Initial Phase3-12 pipeline:
PASS

Human visual:
FAIL

Earliest visual break:
`Phase 07 / MASSES`

Observed failure:
light hair, white clothing, and torso merge into a dominant pale mass. Later phases preserve that damage rather than causing it.

Phase14 also fails fragmentation:
`0.26666666666666666 > 0.2`

This case is not transaction-admitted.

### La-Darknesss

Human visual:
PASS

Phase14 machine:
FAIL

Only failed Phase14 machine check:
fragmentation penalty

Value:
`0.4339622641509434 > 0.2`

No threshold was changed.

### Kaela-Kovalskia

Human visual:
PASS

Phase14 machine:
FAIL

Only failed Phase14 machine check:
fragmentation penalty

Value:
`0.29545454545454547 > 0.2`

No threshold was changed.

### Ouro-Kronii

Phase14:
PASS

A reviewed baseline had already been legitimately adopted as an evaluation baseline.

SA10 hard evidence then found an independent topology failure:
`neck:attached_to:face` missing in the candidate.

Source topology:
PASS

Candidate topology:
FAIL

The baseline adoption record remains valid as an evaluation record. It is not pass authority, and Ouro is not included in the PASS transaction set.

### Shirakami-Fubuki

Phase12:
FAIL

Both conservative and aggressive candidates lose visible part:
`neck`

Conservative silhouette IoU:
`0.989719`

Aggressive silhouette IoU:
`0.988612`

Passing candidate count:
`0`

This is preserved as a Phase12 visible-part survival failure. It is not silently relabeled as an SA10.12 canonical Feature Survival result.

### Tokino-Sora

Human visual:
PASS

Phase14 machine:
FAIL

Failed check:
major-color-mass consistency

Value:
`0.6128011280670762 < 0.65`

No minimum was lowered.

## Failure taxonomy

Observed SA10.16 categories:

- runtime/environment blockers: 0
- Unicode/path I/O failures: 0
- structural decomposition / mass reconstruction: 1
- topology/anatomy: 1 topology failure / 0 anatomy failures
- visible-part survival: 1
- forbidden face detail: 0
- provenance/source-authority failures: 0
- Phase14 visual/machine failures: 4
- diagnostic-only gaps: retained explicitly on admitted cases

The dominant repeated cluster is fragmentation:
- Fuwawa-Abyssgard
- La-Darknesss
- Kaela-Kovalskia

This is the next repair priority.

## Important boundary discovered

Baseline adoption and transaction admission are separate concepts.

Ouro proves the distinction:
- baseline adoption may be valid;
- a later independent hard gate may still fail;
- the case must then remain outside the PASS transaction set.

Therefore baseline adoption is never treated as pass authority.

## Diagnostic boundaries

For newly admitted Okayu and Hoshimachi:

- DINO remains non-authoritative;
- DINO cannot override hard failures;
- SA9 Teacher remains UNAVAILABLE without reviewed annotations;
- explicit SA10.5 Component Survival remains UNAVAILABLE;
- explicit SA10.5 Primitive Economy remains UNAVAILABLE;
- actual-emission evidence remains diagnostic-only;
- actual-emission evidence is not silently mapped to SA10.5.

## Verification

Focused regression chain:
`21/21 PASS`

Covered:
- SA10.14 transaction contract;
- SA10.15 fresh-case admission;
- SA10.16 five-case transaction-set reproducibility;
- canonical payload hashes;
- eight hard gates on Okayu/Hoshimachi;
- failure-taxonomy classifications;
- raw failure-evidence references;
- failed transaction exclusion from PASS set;
- baseline-adoption / transaction-admission separation.

## Production changes

SA10.16 changed no production inference code.

The SA10.15 generic runtime and Unicode-path repairs held across all SA10.16 Drive-backed cases:
- no runtime/environment blocker;
- no Unicode/path I/O blocker.

## Boundaries preserved

- no aggregate quality score;
- no threshold calibration;
- no hard-fail rescue by diagnostics;
- no case-specific production logic;
- no generative img2img;
- no Generative Fill;
- no inpainting;
- no hidden completion;
- no Golden production inference;
- no browser-v12 production inference;
- failed cases are preserved before repair;
- failed transactions are excluded from the PASS set.

## Decision

SA10.16 is complete.

The real PASS transaction cohort is now five cases, and a concrete failure taxonomy exists across eight fresh screened cases.

The evidence is not yet sufficient to justify calibration. The next step is a taxonomy-driven generic repair of the repeated fragmentation cluster while keeping the Phase14 fragmentation threshold unchanged.


## Drive preservation

Canonical folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA10_16_20261007_MULTI_FRESH_CASE`

Drive folder ID:
`1GT0ZYtPvlMgEyfJBoTXIeismvSJmfW1L`

Drive API read-back verified all 54 preserved artifacts.

The preserved set includes:
- eight fresh source images;
- reviewed baseline artifacts for admitted/evaluated cases;
- fresh evaluation outputs for Nekomata-Okayu and Hoshimachi-Suisei;
- visual hard-gate, structural/source-authority, DINO, FaceRasterGuard, fixtures, and passing transactions;
- initial failed-case finals where a Phase12 final existed;
- raw/compact failure evidence for Fuwawa, La+, Kaela, Ouro, Fubuki, and Tokino;
- five-case transaction set;
- SA10.16 failure taxonomy;
- SA10.16 closeout document.

No artifact was preserved outside the canonical `chatGPT及びCodex用` hierarchy.
