# Golden Comparison Event Producer

Status: PHASE 7 PRODUCER IMPLEMENTED

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

The current Phase 7 boundary deliberately stops before transport. A caller can
persist the returned envelope to the Rinka Event Hub ingress once that shared
service has a reachable runtime endpoint. This prevents Minimalizer from taking
a dependency on MCP or ChatGPT transport details.
