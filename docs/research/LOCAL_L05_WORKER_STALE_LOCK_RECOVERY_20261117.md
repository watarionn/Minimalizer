# MinimalizerLocal L05 stale-worker lock recovery — 2026-11-17

## Scope

This change hardens the owner-only LocalWorker runtime without changing the
selected production candidate, image-quality policy, L04 bundle, or rollback
target. The candidate receipt remains `381b0b5a...`; the production baseline
remains `64cfeb76...`.

## Failure addressed

The worker can correctly return HTTP 429 with `Retry-After: 2` while a real
job is active. A hung request, however, can leave the process slot held while
`/health` still reports `ready`. The previous launcher treated that health
response as sufficient and therefore could not recover the stuck slot.

## Source-free implementation

- `local_worker/app.py` records the active endpoint and monotonic job age.
- `/health` now exposes `process.busy`, `process.busy_seconds`, and
  `process.busy_endpoint`.
- The existing parallel-job guard and HTTP 429 contract are unchanged.
- `scripts/start_local_worker.ps1` preserves a healthy active job and exits as
  before. It restarts only when the reported job age is at least 900 seconds,
  and only after resolving the listener on the fixed loopback port 28764.
- The restart remains process-level; it does not forcibly release a live
  Python lock or alter image outputs.

## Verification

Command:

```text
python -m pytest -q tests/test_local_worker.py tests/test_local_l07_pwa_privacy_audit.py tests/test_local_l04_source_stage8_svg_triple_gate.py
```

Result: `57 passed, 1 warning`.

The test set covers the existing 429 parallel-job guard, the new health busy
telemetry, L07 privacy checks, and L04 source/Stage8/SVG contract checks.

## Release status

This is source QA only. It is not a production deployment, not an L04 PASS,
and not evidence for the A/L02 semantic-quality gate. Production process
replacement and current-commit iPhone re-acceptance remain separate gates.
