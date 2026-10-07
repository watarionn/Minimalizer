# SA10.26 tranche2 — deterministic source-bound SVG evidence

Status: IMPLEMENTED / EVIDENCE-ONLY / NO PRODUCTION PROMOTION

The isolated VTracer candidate boundary now has a tiny deterministic SVG
evidence rasterizer. It accepts only filled `path` elements using `M`, `L`,
`C`, and `Z`, plus an optional `translate()` transform. Unsupported SVG
features fail closed. Cubic curves are sampled deterministically.

The rasterized candidate is intersected with the immutable source mask before
measurement (`candidate &= source_mask`). The report records IoU, boundary
recall, source/candidate connected-component counts, and material-topology
preservation. These values are diagnostic evidence only; no VTracer output is
allowed to replace Phase 4/10/12/14 geometry or clear SA10 hard gates.

The tiny synthetic test covers deterministic repeated rasterization, path
syntax, translation, source binding, topology reporting, and rejection of an
unsupported transform. The native worker remains isolated and optional; a
nonzero exit, timeout, missing package, or missing SVG remains an explicit
fallback no-op.

Not performed: VTracer installation, canonical-venv mutation, GC001 visual
promotion, fresh-holdout tuning, Drive write, merge, deployment, or production
rollback. GC001 source silhouette and Phase 4/14 union masks remain the
authoritative hard-gate inputs until a separately reviewed transaction adopts
any candidate.

Verification: focused SA10.26 evidence tests 9 passed; `compileall` passed;
`git diff --check` passed.
