# MinimalizerPublic Unified Gate, Stage 3 (2026-10-09)

Research-only fail-closed acceptance gate for the frozen GC001 and Raden signed originals. Does not modify production, does not override original source-signed Stage8 policies or imply permission to deploy.

## Inputs and evidence
Runs on explicitly supplied evidence JSON: for each exact signed original include source SHA-256, signed source mask manifest SHA-256, full-scene candidate SHA-256, original Stage8 vertices, SVG rendered vertices, shape count, Chromium DPR4 signed owner outside/missing alpha pixels, source-original non-face RGB MAE and independently pinned champion MAE, facial microfeature policy and separate Chrome/Safari/human Golden results. Invalid signatures or absent case data are hard errors. The schema is not an attestation mechanism: callers must first independently verify cryptographic links to the original private signed files, and must not promote self-asserted evidence.

Historical caps remain: GC001 1,887, Raden 1,412 for Stage8 original ring and independently for rendered vertex Gate; 40 total painted/clip shapes. No source ring policy migration is authorized.

## Frozen diagnostic example (reference evidence only, not fresh source validation)
| Gate | GC001 | Raden |
| --- | --- | --- |
| Stage8 input original vertices | 3,604 / 1,887 FAIL | 2,370 / 1,412 FAIL |
| Full-scene signed clip vertices | 5,353 / 1,887 FAIL | 3,586 / 1,412 FAIL |
| Whole-scene shapes | 40 PASS | 40 PASS |
| Chromium DPR4 outside/missing union alpha | 0 / 0 | 0 / 0 |
| 40-shape nonface RGB MAE | 42.012781 (champion 40.318419) FAIL | 21.575139 (champion 24.297144) PASS |
| Face details | disabled | disabled |
| Mobile Safari and human Golden | unverified | unverified |

The candidate is intentionally **NO-GO**. Even if every data field eventually passes, the research evaluator returns release=HOLD and requires independent manual authorization. It cannot automatically merge or deploy.

## Reproduction
`python -W error -m unittest -v test_unified_release_gate` runs four tests: current signed measurements blocked, synthetic all-pass remains manual release only, incomplete/fake signing abort, and invalid numeric type rejected.
`python unified_release_gate.py evidence.json --out gate_result.json` produces a canonical structured gate verdict. Do not publish the private source, original 11 owner mask data or full original Stage8 rings.

## Next implementation boundary
1. Preserve signed contour topology and source ownership without waiving the historical original Stage8 vertex cap; evaluate *truly* fewer source observations, not just fewer SVG command characters.
2. Improve GC001 tie and outfit evidence by structure-aware palette selection within the same 40 shape cap; require independent whole-scene champion checks and human visual review.
3. Validate Mobile Safari and strict same-input Golden before any feature-flag production trial.

Results are only authoritative when tied to actual signed artifacts by SHA and to independent renderer logs. No PR in this research chain is a production promotion.
