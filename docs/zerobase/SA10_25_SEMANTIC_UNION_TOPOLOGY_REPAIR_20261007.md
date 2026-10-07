# SA10.25 Semantic Union Topology Repair — 2026-10-07

Status: IMPLEMENTED / READY FOR REVIEW; real GC001 remains HOLD

## Scope

Phase 14 now evaluates material topology from canonical source-owned semantic
part masks. The shared tiny-component policy is `max(8, round(subject_area *
0.00015))`; raw segmentation specks remain diagnostic evidence and do not
become material topology. `unknown` and `__unbound__` remain outside semantic
ownership.

The Phase 12 source-bound repair and the Phase 14 evaluator use the same
canonical material-mask contract. Phase 14 now exposes `source_topology` as a
hard machine check, covering per-part and semantic-union components, holes,
Euler characteristic, required relations, and source/candidate validation.

## GC001 clean3 verification

Case: `C:\Work\Temp\sa1025-gc001-clean3\GC001_source`

The canonical Phase 14 rerun was deterministic and provenance-valid. Scores:

- silhouette `0.998222`
- boundary recall `0.990224` (from the source-bound artifact)
- major color mass `0.9910241208970547`
- identity `0.995455`
- fragmentation `0.0`
- primitive economy `0.8933333333333333`

The new hard check correctly reports the remaining material semantic-union
mismatch: source holes/Euler `7/-6`, candidate `8/-7`. Therefore the case is
not declared PASS. This is an architectural repair target, not a threshold
or unknown-owner bypass.

## Verification

- focused Phase 14/source-repair/topology tests: `24 passed`
- `python -m compileall -q minimalizer_zerobase tests/zerobase`: PASS
- `git diff --check`: PASS
- real clean3 Phase 14 replay: deterministic/provenance PASS, machine FAIL only
  at the newly enforced `source_topology` union check

Next step is to make the source-owned semantic union replay preserve the union
hole topology while retaining the shared material threshold. Do not weaken the
`0.20` fragmentation limit, assign `unknown` as an owner, or promote this
clean3 result to PASS.
