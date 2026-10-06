# SA7.35 Hard-Gate Path Reconciliation — 2026-10-06

Status: CANONICAL HARD GATE RESTORED / HISTORICAL STALE PASS CLAIMS SUPERSEDED

## Why this stage existed

SA7.34 exposed a contradiction:

- historical GC001 reports after SA7.2 claimed Feature Survival missing=0 and Forbidden Face Detail=0.00%;
- the current production evaluators applied directly to SA7.29/33/34 did not reproduce those values.

SA7.35 traced both evaluation paths and replayed the original inputs.

## Historical canonical path recovered

The original SA7.2 evaluation script used:

- adopted visual baseline: `GC001_silhouette_mass_stage.png`
- source: `GC001.png`
- subject mask: Phase 3 `03_subject_mask.png`
- face mask: Phase 4 `part_masks/face.png`
- survival evaluator: `source_supported_feature_survival_report`
- forbidden-face evaluator: `forbidden_face_detail_ratio`
- every candidate image measured fresh

The source-supported survival rule intentionally requires only adopted-baseline signatures that also exist in the original source. It does not canonize artifacts introduced by older Minimalizer outputs.

## Root cause

The source-supported evaluator existed on the SA7.1/SA7.2 development line but was not retained in current main.

More importantly, later research scripts such as SA7.26 and SA7.29 reused the earlier SA7.2 JSON values instead of recomputing survival and forbidden-face evidence for the current candidate.

That made the copied missing=0 / face=0.00% values stale.

## Fresh replay

Applying the recovered historical inputs and evaluator semantics to all relevant candidates:

| Candidate | Required | Missing | Survival | Forbidden Face Ratio | Face Gate |
| --- | ---: | ---: | --- | ---: | --- |
| SA7.2 | 16 | 0 | PASS | 0.000000 | PASS |
| SA7.29 | 16 | 3 | FAIL | 0.144622 | FAIL |
| SA7.33 | 16 | 3 | FAIL | 0.144622 | FAIL |
| SA7.34 | 16 | 3 | FAIL | 0.144622 | FAIL |

Therefore:

- the original SA7.2 0/0 result is valid;
- the later SA7.29/33/34 0/0 claims were invalid stale reuse;
- SA7.34 did not newly introduce this failure because SA7.29, SA7.33, and SA7.34 produce the same fresh hard-gate result.

## Canonical implementation

SA7.35 restores `source_supported_feature_survival_report` to current main and adds:

- `minimalizer_zerobase/evaluation/canonical_hard_gate.py`
- `tools/run_canonical_hard_gate.py`

The canonical evaluator:

1. requires adopted baseline, current candidate, original source, subject mask, and face mask;
2. measures the current candidate fresh;
3. accepts no previous hard-gate JSON as an input;
4. has no Golden input;
5. reports the exact missing feature signatures;
6. requires forbidden-face ratio exactly 0.0 for this GC001 visual-adoption contract.

Canonical gate version: `sa7.35-v2`.

## Current GC001 missing signatures

SA7.34 fresh canonical result contains three missing source-supported signatures:

1. RGB quantized [16,16,16], area ratio 0.0164962, centroid (0.66633, 0.68545)
2. RGB quantized [16,48,48], area ratio 0.00261614, centroid (0.20491, 0.76166)
3. RGB quantized [144,176,16], area ratio 0.00259797, centroid (0.56070, 0.68088)

These signatures are evidence for the next semantic-attribution stage. They are not permission to hard-code GC001 colors or coordinates into production.

## Corrections

The hard-gate claims in SA7.29, SA7.33, and SA7.34 documentation are explicitly marked superseded where they relied on reused SA7.2 evidence.

The accepted visual baseline remains unchanged.

## Next

SA7.36 Missing Signature Semantic Attribution.

Map the three missing signatures back to authorized semantic source parts and determine which required semantic structures disappeared. Repairs must be semantic-role-based and generic, not RGB/coordinate special cases.
