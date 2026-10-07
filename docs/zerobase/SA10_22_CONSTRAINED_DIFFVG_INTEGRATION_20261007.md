# SA10.22 constrained diffvg integration

Status: IMPLEMENTED / READY FOR REVIEW / PRODUCTION PROMOTION HOLD

SA10.22 reuses the e905517 differentiable geometry foundation and current
`minimalizer_zerobase.refine` proposal machinery. It only updates parameters of
existing `VectorScene` primitives through `apply_geometry_proposals`; it cannot
add, delete, merge, reassign semantic parts, or generate pixels.

Each proposal is evaluated independently. SA10.18 anatomy/silhouette and
SA10.20 topology are hard gates. A proposal is committed only when both pass
and at least one SA10.19 source-shape or SA10.21 regional perceptual score
improves. There is no aggregate-score authority. Any failed proposal remains
rolled back to the current scene.

When `pydiffvg` is unavailable the transaction returns explicit
`backend=fallback_noop`, `optimized=false`, and a rollback result. This is not
reported as an optimized candidate.

## Verification

- `tests/zerobase/test_sa1022_constrained_diffvg.py`: 4 passed
- Synthetic coverage: safe contour move, arm detachment rollback,
  topology-breaking large move rollback, unavailable diffvg fallback
- `python -m compileall -q minimalizer_zerobase`: PASS
- `git diff --check`: PASS

This checkout does not claim a real GC001/Kyoko transaction or production
promotion. The next gate is a real-source transaction with preserved baseline,
per-proposal evidence, mandatory visual artifacts, deterministic replay, and
independent review. No push, merge, deploy, or Drive write is part of SA10.22.
