# Local L05 owner-PC private HTTPS replay (2026-11-07)

**Actual owner-PC replay evidence. L05 remains HOLD; production remains
NO_GO.** The private tailnet hostname, raw source, response bodies and PNG
files remain outside GitHub. This note stores only source-free measurements and
hashes.

## Observed live results

- LocalWorker loopback `/health`: HTTP 200, `ready=true`, worker
  `local-compute-v1`, active/best route `zerobase2`, ZeroBase2 authorized.
- Private HTTPS `/health`: HTTP 200 with the same readiness payload.
- Private HTTPS `/api/v2/minimalize` with the signed H06 WebP source:
  HTTP 200, `Content-Type: image/png`, source size `2000x2000`, output size
  `400x400`, processing `52904.7ms`, output PNG SHA-256
  `f5df72ca78e173b49c830d9e5724e26acfed18f9dc9667a713cd9edd12c64834`.
  The input source SHA-256 was
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.
- A second and third V2 request also returned HTTP 200 PNG, with processing
  `51788.5ms` and `51133.9ms` respectively. They did not return the expected
  busy response.
- Private HTTPS `/api/zerobase2/minimalize`: HTTP 503 with
  `X-Minimalizer-Failure-Class: runtime`; the response body was not a PNG.
  This is a real fallback-triggering failure, not a fabricated success.
- Invalid upload content type: HTTP 415 with the expected rejection body.

## Concrete failure

The live worker did **not** produce HTTP 429 plus `Retry-After: 2` for a
concurrent second request. Requests were serialized and both completed with
HTTP 200. The cause is that the current live worker executes its CPU-bound
function synchronously inside an `async def`, blocking the event loop before a
second request can reach the non-blocking process-lock check.

The Draft branch contains the bounded correction in commit `66aeee60`:
`asyncio.to_thread` surrounds both CPU-heavy routes, and
`tests/test_local_worker_concurrency.py` verifies that the second concurrent
request receives HTTP 429 and `Retry-After: 2`. Focused A/B source QA after the
change is **52 passed**. The live Worker was not modified by this replay.

## Gate decision and next action

- Actual PC/private HTTPS: **partial evidence, FAIL on concurrent 429**.
- PNG input/output and ZeroBase2 fallback: observed.
- iPhone acceptance: **not attempted**; defer until production reflection.
- L05 formal: `HOLD`; production: `NO_GO`.

After an owner-authorized activation of the Draft LocalWorker fix, rerun the
private HTTPS replay and require a real 429/Retry-After readback before marking
the owner-run receipt complete. Do not merge or promote from this partial
receipt.
