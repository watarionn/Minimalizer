# SA10.24 Source-Bound Boundary and Topology Repair — 2026-10-07

Status: HOLD / ARCHITECTURAL BLOCKER

## Blocker addressed

SA10.23 exposed a real GC001 candidate with silhouette IoU `0.98948` but
source outer-boundary recall `0.6235384320490703 < 0.90`. The same candidate
also changed arm component/Euler topology. The hard gates remain unchanged:
outer-boundary recall `0.90`, topology equality, source anatomy, and
fragmentation maximum `0.20`.

## Repair

`structural_source_repair.py` is now `sa10.24-v1`. Before candidate emission it
compares source-owned part topology and the source/candidate outer boundary.
Every visible semantic owner with a legitimate Phase 12 owner group is eligible;
`unknown` remains fail-closed without such an owner. Repair is deterministic
replay of the Phase 4 source masks. The repair report records the pre-repair boundary recall,
topology reasons, and the existing relation evidence. No case name, coordinate,
color, threshold, or generated pixel is introduced.

## Verification

- SA10.24 focused structural-repair and related gate tests: 17 passed; the dedicated repair file is 8 passed.
- Full suite was attempted with the canonical venv and stopped at collection because `tests/test_differentiable_geometry.py` requires unavailable `torch`.
- `python -m compileall -q minimalizer_zerobase ...`: passed.
- `git diff --check`: passed.
- Fresh clean2 output: `C:\Work\Temp\sa1024-gc001-clean2\GC001_source`.
- Real machine checks: silhouette `0.999148` PASS, source boundary recall `0.9641556450` PASS, fragmentation `0.075` PASS, major color mass `0.9910241209` PASS, determinism PASS. Known semantic topology passes; overall topology remains blocked only by visible Phase 4 `unknown` pixels without a legitimate Phase 12 source-owned group, and the derived union mismatch.

## Review boundary

This change is local only. No Drive update, push, merge, deploy, or production
promotion was performed. The next step is to resolve the Phase 4 to Phase 12
unknown ownership contract; do not weaken gates or replay unknown implicitly.
