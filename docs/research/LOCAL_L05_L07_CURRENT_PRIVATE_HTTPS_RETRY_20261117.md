# Local private HTTPS current retry evidence — 2026-11-17

This is a source-free operational recheck against the adopted production
Worker. It records the current PC private-HTTPS evidence and failure paths;
it does not promote the L04 bundle or replace the owner iPhone acceptance
receipt.

## Binding

- Production Worker commit: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- Candidate receipt: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- Route: `zerobase2`
- Profile: `reviewed-sa10`
- Input case: H04 signed source
- Input SHA-256:
  `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`

## Observed responses

The health endpoint returned HTTP 200 with `status=ready`,
`active_production_route=zerobase2`, and `zerobase2_authorized=true`.

Two private-HTTPS submissions to the production ZeroBase2 endpoint while the
single-worker slot was occupied returned:

- HTTP status: `429 Too Many Requests`
- `Retry-After: 2`
- response media type: `application/json`
- response body length: 46 bytes

The response is consistent with the fail-closed single-job concurrency
contract. No retry loop was added to the worker by this recheck.

The same signed H04 input was also replayed through both current PNG routes:

- `zerobase2`: HTTP 200, `image/png`, output SHA-256
  `b0b2717588ce8e01f4c95609bbe139dd161670b74da1898b6c359891d8d9567a`
- `v2`: HTTP 200, `image/png`, output SHA-256
  `e4d3cc859018677453bbd8364b3a9f1152c9e6c2fbffab22a2124586d07402a1`

The input SHA in both responses matched the signed H04 source SHA above. The
owner-side L05 receipt records input/output file readback and the following
failure paths: invalid media type HTTP 415, busy HTTP 429 with
`Retry-After: 2`, and invalid image HTTP 503. The existing receipt auditor
reported `owner_pc_e2e_verified=true`, `png_routes_verified=true`,
`failure_paths_verified=true`, and `file_readback_verified=true`.

The current Worker adoption receipt separately records a v2 fallback replay
with the same candidate and Worker binding. That is retained as fallback
evidence, not silently treated as part of the new PC run.

## Gate interpretation

This proves current PC private-HTTPS PNG success, the retry signal, and the
recorded failure paths on the adopted Worker. It does not prove SVG delivery,
L04 formal PASS, or current-commit iPhone acceptance. The auditor therefore
keeps `L05_formal=HOLD`, `production_release=NO_GO`, and
`release_authorized=false`. Existing successful replay, fallback, and
rollback evidence remains bound to its recorded receipts and must not be
silently rebound to another commit.
