# SA10.26 tranche1 — VTracer source-bound candidate boundary

Status: IMPLEMENTED / OPTIONAL BACKEND / NO PRODUCTION PROMOTION

Tranche1 adds an explicit adapter boundary for a future VTracer candidate
generator. VTracer is optional and is not installed automatically. The adapter
accepts an immutable source mask and an already-authorized semantic mask only;
it never assigns semantic ownership and never changes visible output.

The result is fail-closed and records source/authorized-mask SHA-256 values.
Missing authorization, shape mismatch, pixels outside the source, and an
unavailable backend produce an explicit `no-op` or `unavailable` result. This
is not a successful candidate and cannot clear SA10.18 anatomy/silhouette,
SA10.20 topology, SA10.25 material-topology, provenance, color, identity, or
fragmentation hard gates. Rollback is therefore represented as no visible
change; existing production and baseline artifacts remain untouched.

Verification:

- `PYTHONPATH=. pytest -q tests/zerobase/test_sa1019_source_shape_evidence.py` — 5 passed
- `python -m compileall -q minimalizer_zerobase` — PASS
- `git diff --check` — PASS

Not performed in tranche1: VTracer package installation, canonical-venv
mutation, real GC001 candidate generation, fresh-holdout tuning, full
ZeroBase rerun, Drive write, commit, push, merge, deployment, or production
rollback. Those require a separate reviewed gate after the adapter contract
and backend API are approved.
