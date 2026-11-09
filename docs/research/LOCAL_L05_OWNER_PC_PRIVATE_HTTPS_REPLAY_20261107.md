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

## CMD loopback recheck after protected-runtime restoration

The owner reran the signed H06 WebP through the protected LocalWorker loopback
from `cmd.exe` after the Draft replay was complete. The private HTTPS request
without the owner identity header correctly returned HTTP 403 and was not
counted as a generation failure. The loopback recheck returned a successful
PNG response with `Content-Type: image/png`, source size `2000x2000`, output
size `400x400`, processing `61632.5ms`, and output PNG SHA-256
`f5df72ca78e173b49c830d9e5724e26acfed18f9dc9667a713cd9edd12c64834`.
The input source SHA-256 remained
`c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.
The receipt files remain in the owner's private temporary directory outside
GitHub. This is loopback runtime evidence, not private-HTTPS owner acceptance
and not physical iPhone acceptance.

## Post-activation replay

After the owner temporarily disabled the Startup launcher for the old worker,
the Draft #451 worker was started from its isolated worktree on the existing
loopback port. Tailscale Serve remained unchanged and continued to proxy the
private HTTPS port to `127.0.0.1:28764`.

- The first concurrent V2 request returned HTTP 200 `image/png`, source size
  `2000x2000`, output size `400x400`, processing `52944.1ms`, and output PNG
  SHA-256
  `f5df72ca78e173b49c830d9e5724e26acfed18f9dc9667a713cd9edd12c64834`.
- The second concurrent V2 request returned HTTP 429 with
  `Retry-After: 2` and the busy response body. Its response was not treated as
  an image.
- The private HTTPS origin was echoed by CORS, and the saved PNG and busy body
  were read back from the owner-PC receipt directory.
- The signed H06 input SHA-256 remained
  `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`.

This is the first actual private-HTTPS concurrency receipt after the
`asyncio.to_thread` correction in `66aeee60` (included in PR head
`b5c6747af1dd40cb686d9fd0be8ca78b935022d5`).

## Concrete failure

Before activation, the live worker did **not** produce HTTP 429 plus
`Retry-After: 2` for a concurrent second request. Requests were serialized and
both completed with HTTP 200. The cause was that the old live worker executed
its CPU-bound function synchronously inside an `async def`, blocking the event
loop before a second request could reach the non-blocking process-lock check.

The Draft branch contains the bounded correction in commit `66aeee60`:
`asyncio.to_thread` surrounds both CPU-heavy routes, and
`tests/test_local_worker_concurrency.py` verifies that the second concurrent
request receives HTTP 429 and `Retry-After: 2`. Focused A/B source QA after the
change is **52 passed**.

## Gate decision and next action

- Actual PC/private HTTPS after Draft activation: **PASS for concurrent 429 and
  Retry-After readback**.
- PNG input/output and ZeroBase2 fallback: observed.
- iPhone acceptance: **not attempted**; defer until production reflection.
- L05 formal: `HOLD`; production: `NO_GO`.

The concurrency receipt is complete for the owner-PC private HTTPS replay. Do
not merge or promote from this evidence alone: the physical iPhone acceptance
and remaining L05 release gates are still separate.

## 2026-11-09 protected loopback smoke readback

Without changing the worker configuration, the currently running protected
Loopback Worker was read back once from `127.0.0.1:28764`:

- `/health`: HTTP 200, `ready=true`, `worker=local-compute-v1`, active route
  `zerobase2`, `zerobase2_authorized=true`.
- `/api/v2/minimalize` with the repository test image
  `Oozora-Subaru_list_thumb.png`: HTTP 200, `Content-Type: image/png`,
  response size `3774` bytes, output SHA-256
  `9f8b7c5d2940a416559b52cda0ec393372d49d0ea351be8bd7b9c6234a7cc49e`.
- A second `/health` read after processing remained HTTP 200 and ready.

This is a loopback runtime smoke receipt only. It is not private-HTTPS
acceptance, production reflection, or iPhone acceptance; L05 remains `HOLD`
and production remains `NO_GO`.
