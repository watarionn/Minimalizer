# Handoff: SA10.22 constrained diffvg

Status: IMPLEMENTED / READY FOR REVIEW

The constrained transaction is in
`minimalizer_zerobase/refine/constrained_diffvg.py`. Before any production
promotion, run one real GC001 and one Kyoko transaction from the canonical
SA10 production path. Preserve the source, baseline, every proposal result,
hard-gate report, source-shape evidence, regional perceptual evidence, and
deterministic replay hashes. Review visual artifacts independently.

Required next checks:

1. Confirm `pydiffvg` availability and record the exact backend status.
2. Run GC001/Kyoko with SA10.18 and SA10.20 as immutable hard constraints.
3. Confirm at least one SA10.19/SA10.21 improvement without protected-objective
   regression; do not use an aggregate score to authorize adoption.
4. Keep failed proposals and rollback reasons in the transaction artifact.
5. Only after review may a separate production-promotion task be opened.

No production switch, push, merge, deployment, or Drive save is authorized by
this handoff.
