# SA10.14 Hard-Gate Closure & Regression Transaction Integration — 2026-10-07

Status: COMPLETE / REPRODUCIBLE REGRESSION TRANSACTION / NON-GC001 HARD-GATE CHAIN CLOSED

## Goal

Integrate the independently validated non-GC001 hard-evidence chain into one deterministic regression transaction per case without introducing an aggregate quality score or allowing diagnostics to rescue hard failures.

## Implementation

Added:

- `minimalizer_zerobase/evaluation/regression_transaction.py`
- `tools/run_sa1014_regression_transaction.py`
- `tests/zerobase/test_sa1014_regression_transaction.py`
- `tests/zerobase/test_sa1014_real_transactions.py`

The transaction binds and cross-checks:

- immutable SA10.12 adopted-baseline record;
- fresh source file SHA-256;
- fresh Phase12 candidate SHA-256;
- SA10.14 visual hard-gate binding;
- Feature Survival;
- Forbidden Face Detail;
- Source Authority;
- Anatomy;
- Topology;
- Phase14 machine result;
- Phase14 human visual result;
- Phase14 determinism result and determinism SHA;
- exact-output DINO diagnostic;
- SA10.13 FaceRasterGuard evidence.

Every source/candidate reference must resolve to the same source and candidate SHA. Any cross-link mismatch fails the transaction.

## Transaction authority

Hard evidence is individually visible:

1. Feature Survival
2. Forbidden Face Detail
3. Anatomy
4. Topology
5. Source Authority
6. Phase14 machine
7. Phase14 human visual
8. Determinism

`pass_transaction` is the logical conjunction of those hard results plus evidence-link validity.

This is not an aggregate quality score.

Diagnostics do not participate in hard-pass rescue:
- DINO semantic retention remains non-authoritative;
- adaptive complexity remains diagnostic;
- component / primitive diagnostics retain their previous authority boundary;
- SA9 Teacher evidence remains UNAVAILABLE where no reviewed annotation exists.

## Synthetic negative regression

Synthetic negative transactions prove that perfect diagnostics cannot rescue:

- Forbidden Face Detail FAIL;
- Anatomy FAIL;
- Source Authority FAIL.

A candidate/source/evidence cross-link mismatch also fails the transaction.

## Hyakuto-Kyoko

Transaction ID:
`sa10.14-regression-hyakuto-kyoko-20261007-v1`

Source SHA-256:
`cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`

Candidate SHA-256:
`84022e48e13ed7a80f8e3425d085d311e3ab7c86fcb28278ba079e182a33646a`

Adopted baseline SHA-256:
`294a77a025656391a76b35cbb2fdb7f8f59c0e176e8433a1da0ca1fa5299065b`

Phase14 determinism SHA-256:
`44eabdd61953d51966d363ba0014907f757d3d43f3de485da5272fd7eb9c76b6`

Result:
- all evidence links: PASS
- all 8 hard gates: PASS
- transaction: PASS

Canonical transaction payload SHA-256:
`41e1400c8a7f88b950f006aa520e5626df2b68bb1c113d3ee8ff2bce5b46c79c`

Canonical artifact:
`benchmarks/regression/sa10/transactions/Hyakuto-Kyoko.sa10.14-transaction.json`

## Juufuutei-Raden_stylecal_source

Transaction ID:
`sa10.14-regression-juufuutei-raden-20261007-v1`

Source SHA-256:
`64022608d65006e7984a556c7140a3880a76b434e42b4ec9b3f48441dfeb87e3`

Candidate SHA-256:
`576a7baa1cf2dcf1a3254fb7daecefb1f5520dc8833294924077ba8ef98ab4b5`

Adopted baseline SHA-256:
`a31acc69a055e4144484939a510f06dee61379e426dc0b39751f4a5cf90dd07f`

Phase14 determinism SHA-256:
`f5e6ed30048508d6e36734d37685ec5557798c2ff827fa3792bbf8068db64961`

Result:
- all evidence links: PASS
- all 8 hard gates: PASS
- transaction: PASS

Canonical transaction payload SHA-256:
`5e2bb0ef5f309fe415002cafd49ecdca69fbbf8e18bfc3d8a7b45ecf185f4738`

Canonical artifact:
`benchmarks/regression/sa10/transactions/Juufuutei-Raden_stylecal_source.sa10.14-transaction.json`

Raden's known macro emission gap remains separate:
- actual emission realization: 0.5;
- diagnostic-only: true;
- SA10.5 Component Survival: UNAVAILABLE;
- SA10.5 Primitive Economy: UNAVAILABLE.

The transaction does not reinterpret actual-emission evidence as SA10.5 authority.

## Self-describing transaction

Each transaction now stores:

- adopted baseline artifact ID / SHA;
- adoption transaction ID;
- evaluation transaction ID;
- Phase14 machine / human / determinism state;
- Phase14 determinism SHA;
- evidence schema versions;
- source/candidate SHA;
- hard evidence list;
- diagnostic evidence;
- evidence-link checks.

The transaction can therefore be audited without guessing which evidence generation it represents.

## Portable canonical payload hashing

Transaction payload hashes are defined over:

`json.dumps(payload, indent=2, sort_keys=True) + "\n"`

encoded as UTF-8.

The runner writes canonical bytes directly with `write_bytes` to avoid Windows CRLF translation ambiguity.

Transaction set:
`benchmarks/regression/sa10/SA10_14_transaction_set.json`

The set contains canonical payload SHA-256 values rather than platform-specific checked-out file-byte hashes.

## Verification

Local pre-self-description focused chain:
- 27/27 PASS

GitHub Actions final self-describing chain:
- 29/29 PASS
- workflow run: `37584058272`
- Python 3.12
- Linux / opencv-python-headless

The first temporary CI run intentionally caught a canonical-hash definition mismatch. The hash contract was corrected, then the second run passed 29/29.

The temporary verification workflow was removed after success and is not part of the final main-branch change.

## Boundaries preserved

- no aggregate quality score;
- no diagnostic hard-fail override;
- no new calibrated threshold;
- candidate self-reference forbidden;
- adopted baseline remains evaluation-only;
- Golden not used for production inference;
- browser fallback not used for production inference;
- FaceRasterGuard remains source-only and Phase4-face-mask bounded;
- no generation / inpainting / hidden completion;
- SA9 Teacher evidence remains unavailable without reviewed annotation;
- Raden emission-gap evidence remains diagnostic-only.

## Decision

SA10.14 is complete.

The non-GC001 hard-gate chain is now reproducible as a deterministic, auditable transaction for Kyoko and Raden. The next step should expand the transaction protocol to a fresh third case before considering any cross-case calibration.
