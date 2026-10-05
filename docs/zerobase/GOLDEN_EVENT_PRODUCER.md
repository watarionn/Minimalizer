# Golden Comparison Event Producer

Status: P3 RUNTIME WIRED / LIVE E2E PENDING

The producer boundary converts an already-computed Golden Gap report into
`rinka.event/1.0` without changing evaluation semantics.

Event: `minimalizer.golden.evaluated`

## Runtime boundary

Current `main` audit entering P3 found that `deliver_shadow()` and
`evaluate_golden_gap()` were implemented and unit-tested but were not connected
through a real runtime callsite.

P3 introduces `minimalizer_zerobase/golden_comparison/runtime.py` as the
canonical post-evaluation boundary:

```text
evaluate_golden_gap()
        ↓ valid native report
build_golden_evaluated_event() exactly once
        ↓ frozen envelope
deliver_shadow()
        ↓
optional Rinka Event Hub ingress
```

`evaluate_golden_runtime()` is the normal environment-wired callsite.
It reads only the presence/content needed by the HTTP sender from
`RINKA_EVENT_HUB_URL` and `RINKA_EVENT_HUB_TOKEN`; secret values are never
placed in reports, events, errors, or logs by this boundary.

`retry_golden_shadow()` retries delivery using the exact event object created
for the completed evaluation. It does not re-evaluate and does not rebuild the
envelope, so `occurred_at` and the deterministic event identity cannot drift
between attempts.

## Design rules

- Golden evaluation remains pure and deterministic.
- The evaluator does not import Event Hub or perform network I/O.
- Event construction happens only after a Golden Gap report exists.
- Native evaluation errors still fail closed.
- Once a valid native report exists, Event Hub integration is fail-open.
- Event construction/configuration/delivery faults cannot invalidate that report.
- First evaluation has `previous_score=null`, `delta=null`, verdict `evaluated`.
- Later evaluations derive `improved`, `regressed`, or `unchanged`.
- PASS/FAIL hard gate and hard failures are preserved separately from diagnostic mean.
- Cross-case comparisons fail closed inside the producer contract.
- Artifacts remain references; raster data is never placed in the event payload.
- Default event identity is retry-stable: the same `run_id + case_id` produces the same event ID.
- Events from the same run share a deterministic correlation ID.
- Explicit caller-provided event/correlation IDs still take precedence.
- A completely unconfigured shadow sender is a no-op.
- Partial/invalid Event Hub configuration is contained after native evaluation.

## P3 verification

Integration coverage now exercises the real runtime boundary rather than only
producer/client unit tests:

- successful runtime evaluation and HTTP sender path;
- Event Hub outage does not fail native evaluation;
- post-report event-construction errors are contained;
- disabled shadow mode is a no-op;
- partial environment configuration is fail-open;
- retry sends the exact serialized envelope from the original evaluation.

The dedicated `rinka-event-shadow` workflow includes the runtime integration
tests on pull requests and on relevant pushes to `main`.

Remaining P3 evidence before closure:

1. CI PASS on the integration change.
2. One production-safe live delivery through the runtime boundary.
3. Event Hub ingestion evidence for the first delivery and duplicate retry.
4. Evidence preservation and merge.

The shared Event Hub remains the owner of MCP/ChatGPT transport details.
Minimalizer owns only the completed Golden evaluation fact and optional delivery
of that fact.
