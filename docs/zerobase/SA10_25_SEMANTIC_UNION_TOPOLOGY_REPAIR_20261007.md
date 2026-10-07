# SA10.25 Material Topology Consolidation — 2026-10-07

Status: CLOSED / MACHINE HARD GATES PASS

SA10.25 resolves the SA10.24 conflict between source-topology fidelity and the unchanged Phase14 fragmentation limit. Candidate generation and evaluation now share one deterministic material-topology definition based on the existing Phase14 tiny-component policy (`max(8, round(subject_area * 0.00015))`). No GC001-specific threshold or branch was added.

## Implementation

- Shared `material_topology` evidence normalizes sub-threshold segmentation components and enclosed pinholes while preserving material-sized components and holes.
- Structural source repair replays canonical material masks rather than raw segmentation noise.
- Semantic-union topology is repaired in addition to per-part topology. `unknown` remains non-semantic; observed unassigned source pixels may travel through an explicit `__unbound__` coverage carrier and never acquire semantic graph authority.
- Phase14 source-mask replay uses the same canonical material threshold as fragmentation evaluation. This removes the evaluator/diagnostic mismatch where raw Phase4 noise had been counted only by Phase14.
- `source_topology` is now an explicit hard machine check and contributes to `machine_pass`.
- Existing fragmentation maximum `0.20`, source boundary minimum `0.90`, anatomy, provenance, semantic relation, color, identity, and silhouette gates are unchanged.
- No generated visible pixels, case-name branch, fixed coordinate, fixed color, or fixed mask logic was introduced.

## Real GC001 clean4

Canonical source: `C:\Work\Temp\macro-gc001\GC001_source.png`.

Final machine result:

- machine_pass: `true`
- fragmentation penalty: `0.0` PASS, 37 components / 0 tiny, threshold 8
- source boundary recall: `0.9902242668200115` PASS
- source topology: PASS, no mismatches
- major color mass consistency: `1.0` PASS
- identity feature retention: `0.998418` PASS
- silhouette preservation: `0.998441` PASS
- all Phase14 machine checks including explicit `source_topology`: PASS

Human visual review remains independent and is not converted into an automatic PASS by this stage.

## Verification

- focused structural / Phase14 tests: 23 passed
- full `tests/zerobase`: 900 passed
- `compileall`: PASS
- `git diff --check`: PASS
- generated GC001 evidence remains outside Git

## Next

SA10.26 should perform independent visual comparison of the real GC001 source and clean4 output, rerun the established PASS transactions plus an untouched fresh holdout, preserve comparison evidence under the canonical Drive hierarchy, then decide whether this candidate is eligible for production promotion. Do not promote on machine gates alone.
