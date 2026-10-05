# Golden Comparison Event Producer

Status: P3 CLOSED / LIVE E2E PASS

The producer boundary converts an already-computed Golden Gap report into
`rinka.event/1.0` without changing evaluation semantics.

Event: `minimalizer.golden.evaluated`

## Runtime boundary

The P3 audit of the pre-change `main` found that `deliver_shadow()` and
`evaluate_golden_gap()` were implemented and unit-tested but were not connected
through a real runtime callsite.

P3 adds `minimalizer_zerobase/golden_comparison/runtime.py` as the canonical
post-evaluation boundary:

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
It reads only the values required by the HTTP sender from
`RINKA_EVENT_HUB_URL` and `RINKA_EVENT_HUB_TOKEN`; secret values are never
placed in reports, events, errors, or logs by this boundary.

`retry_golden_shadow()` retries delivery using the exact event object created
for the completed evaluation. It does not re-evaluate and does not rebuild the
envelope, so `occurred_at` and deterministic event identity cannot drift
between attempts.

`ShadowDeliveryResult.state` preserves the non-secret Event Hub result state
such as `STORED` or `DUPLICATE` for operational evidence without changing
delivery authority.

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

## P3 integration verification

PR #122 exercises the real runtime boundary rather than only producer/client
unit tests.

Dedicated `rinka-event-shadow` CI:
- workflow run: `37262453524`
- pinned runtime commit used by the production proof: `6c21d3ffbf29cf88cb368abc7c0c18dabc7d1056`
- result: **23 passed**
- covered: successful HTTP delivery, retained Hub state, outage fail-open,
  post-report integration failure containment, disabled/partial configuration,
  and exact-envelope retry.

## Production-safe E2E evidence

Rinka Event Hub production service: `rinka-local-operator`.

The Event Hub P3 diagnostic was merged by PR #17 at commit
`46be5a28a269907e7ff7c302d9fbe5be2e459ce3`. The diagnostic was opt-in and
loaded the exact Minimalizer runtime modules from immutable commit
`6c21d3ffbf29cf88cb368abc7c0c18dabc7d1056` into a temporary directory.
The production Event Hub token stayed inside the Render process and was not
printed, persisted, or copied into the repository.

Observed production log at `2026-10-05T04:17:31.744133132Z`:

```text
P3_RUNTIME_SELFTEST=PASS,STORED,DUPLICATE,same_event_id=True,event_id=evt_3970f8ca488ea5da5cf37916e3c9a4fc,minimalizer_commit=6c21d3ff
```

This proves:
- native Golden Gap evaluation completed with `PASS`;
- the real Minimalizer runtime built and delivered `minimalizer.golden.evaluated`;
- first production ingress returned `STORED`;
- retry of the same frozen envelope returned `DUPLICATE`;
- retry retained the same event identity.

`RINKA_P3_RUNTIME_SELFTEST` was returned to `0` immediately after evidence
capture. The diagnostic remains opt-in and performs no action during normal
operation.

## P3 decision

The first Minimalizer Event Hub producer is production-safe for the tested
boundary.

P3 acceptance sequence is complete:
1. actual `deliver_shadow` callsites audited;
2. real Golden evaluation completion boundary identified;
3. `minimalizer.golden.evaluated` wired there;
4. Event Hub failures remain fail-open after native evaluation;
5. exact envelope is reused across retries;
6. real-callsite integration tests added;
7. CI passed;
8. production-safe E2E passed;
9. ingestion/dedup evidence preserved;
10. merge is the final repository action.

The shared Event Hub remains the owner of MCP/ChatGPT transport details.
Minimalizer owns only the completed Golden evaluation fact and optional delivery
of that fact.
