# Golden Comparison Event Producer

Status: P2 SHADOW HARDENING IN PROGRESS

The producer boundary converts an already-computed Golden Gap report into
`rinka.event/1.0` without changing evaluation semantics.

Event: `minimalizer.golden.evaluated`

Design rules:

- Golden evaluation remains pure and deterministic.
- The evaluator does not import Event Hub or perform network I/O.
- Event construction happens only after a Golden Gap report exists.
- First evaluation has `previous_score=null`, `delta=null`, verdict `evaluated`.
- Later evaluations derive `improved`, `regressed`, or `unchanged`.
- PASS/FAIL hard gate and hard failures are preserved separately from diagnostic mean.
- Cross-case comparisons fail closed.
- Artifacts remain references; raster data is never placed in the event payload.
- Default event identity is retry-stable: the same `run_id + case_id` produces the same event ID.
- Events from the same run share a deterministic correlation ID.
- Explicit caller-provided event/correlation IDs still take precedence.
- Shadow delivery is observational and fail-open.
- Event Hub/network failure is returned as shadow delivery state and never raises into the native Minimalizer evaluation path.
- A disabled shadow sender is a no-op.

P2 gate mapping:

- G6 real ChatGPT subscription lifecycle: separate integration exercise.
- G7 Minimalizer shadow pilot: producer and fail-open delivery boundary implemented; live Hub ingress wiring remains.
- G8 Hub outage does not stop native Minimalizer: boundary invariant implemented and covered by outage tests; end-to-end native-run outage exercise remains.

The shared Event Hub remains the owner of MCP/ChatGPT transport details. Minimalizer
only constructs the envelope and invokes an optional shadow sender after evaluation.
