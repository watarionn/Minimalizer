# SA10.24 Source-Bound Topology Repair — 2026-10-07

Status: CLOSED WITH ARCHITECTURAL BLOCKER

SA10.24 moved structural preservation into candidate generation without weakening any existing hard threshold. Phase 12 now compares source-owned semantic-part topology and source boundary evidence and conservatively replays legitimate source-owned groups when simplification changes material structure. The policy is generic: no GC001 case branch, fixed coordinate, fixed color, fixed mask, or generated pixels.

## Real GC001 result

Canonical source SHA-256 remains `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.

Latest real candidate evaluation after the source-bound repair:

- source boundary recall: `1.0` PASS (`>= 0.90`)
- silhouette preservation: `0.999148` PASS
- major color mass consistency: `0.9910241208970547` PASS
- identity feature retention: `0.995455` PASS
- part layout mean: approximately `0.99994` PASS
- known source-owned semantic parts are restored to source topology before final evaluation
- fragmentation penalty: `0.50` FAIL (`> 0.20`)
- remaining semantic-union topology mismatch: source holes/Euler `9/-8` versus candidate `11/-10`

The earlier intermediate `0.075` fragmentation note is superseded by this final re-evaluation of the current Phase 12 artifact and code.

## Contract clarification

Phase 4 `unknown` is defined as `subject & ~assigned`, an unclassified residual rather than a legitimate semantic owner. It is therefore not a source-owned per-part replay target. It is not fabricated in Phase 12. Full source shape remains independently protected by silhouette and source-boundary hard evidence.

## Architectural blocker

Blindly replaying every source segmentation fragment is not a valid solution: it restores segmentation-noise topology but drives fragmentation to `0.50`, violating the unchanged `0.20` hard threshold. SA10.24 therefore stops at the correct boundary rather than weakening either gate.

SA10.25 must distinguish material topology from segmentation-noise topology, or consolidate primitives while preserving material connectivity/holes. It must keep the fragmentation threshold at `0.20`, retain source boundary/anatomy authority, and must not add generated visible content.

## Verification

- focused structural/source tests: `12 passed` in canonical venv after the authority-contract change
- previous SA10.24 full ZeroBase regression before the final authority-only edit: `889 passed`
- generated real artifacts remain outside Git
