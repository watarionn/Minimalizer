# SA10.24 Source-Bound Boundary and Topology Repair — 2026-10-07

Status: IMPLEMENTED / READY FOR RINKA RE-REVIEW

## Blocker addressed

SA10.23 exposed a real GC001 candidate with silhouette IoU `0.98948` but
source outer-boundary recall `0.6235384320490703 < 0.90`. The same candidate
also changed arm component/Euler topology. The hard gates remain unchanged:
outer-boundary recall `0.90`, topology equality, source anatomy, and
fragmentation maximum `0.20`.

## Repair

`structural_source_repair.py` is now `sa10.24-v1`. Before candidate emission it
compares source-owned part topology and the source/candidate outer boundary.
Only implicated semantic owners are repaired by deterministic replay of their
Phase 4 source masks. The repair report records the pre-repair boundary recall,
topology reasons, and the existing relation evidence. No case name, coordinate,
color, threshold, or generated pixel is introduced.

## Verification

- SA10.24 focused ZeroBase tests: 32 passed.
- Full `tests/zerobase`: 889 passed.
- `python -m compileall -q minimalizer_zerobase ...`: passed.
- `git diff --check`: passed.
- A fresh real GC001 Phase 3–14 replay was not run in this checkout; the
  canonical source remains the externally documented
  `C:\Work\Temp\macro-gc001\GC001_source.png`.

## Review boundary

This change is local only. No Drive update, push, merge, deploy, or production
promotion was performed. The next step is independent review and, if approved,
a fresh GC001 replay with mandatory artifacts and hard-gate evidence.
