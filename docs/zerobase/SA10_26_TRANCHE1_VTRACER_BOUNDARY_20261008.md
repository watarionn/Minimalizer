# SA10.26 tranche1 — VTracer source-bound candidate boundary

Status: IMPLEMENTED / OPTIONAL BACKEND / NO PRODUCTION PROMOTION

Tranche1 adds an explicit subprocess boundary for the optional VTracer
candidate generator. The parent process never imports the native `vtracer`
extension. A worker alone calls `convert_image_to_svg_py`, with an immutable
authorized mask serialized to PNG and a 15-second timeout.

The result is fail-closed and records source/authorized-mask SHA-256 values.
Missing authorization, shape mismatch, pixels outside the source, worker
nonzero/native crash, timeout, and missing SVG produce an explicit
`fallback_noop` result. A successful SVG is still a non-authoritative
`no-op` candidate. Every worker result records `isolated=true`, exit code when
available, source/mask SHA-256 values, and the MIT/Apache-2.0 license boundary.
This
is not a successful candidate and cannot clear SA10.18 anatomy/silhouette,
SA10.20 topology, SA10.25 material-topology, provenance, color, identity, or
fragmentation hard gates. Rollback is therefore represented as no visible
change; existing production and baseline artifacts remain untouched.

Verification:

- `C:\Work\Projects\Minimalizer\.venv\Scripts\python.exe -m pytest -q tests/zerobase/test_sa1019_source_shape_evidence.py` — 7 passed
- `python -m compileall -q minimalizer_zerobase` — PASS
- `git diff --check` — PASS
- canonical venv tiny synthetic PNG, two runs — identical SVG SHA-256, PASS

Not performed in tranche1: package installation, canonical-venv mutation, real
GC001 candidate generation, fresh-holdout tuning, full ZeroBase rerun, Drive
write, merge, deployment, or production rollback. The SVG remains an evidence
candidate and cannot pass the SA10 hard gates or production promotion by
itself.
