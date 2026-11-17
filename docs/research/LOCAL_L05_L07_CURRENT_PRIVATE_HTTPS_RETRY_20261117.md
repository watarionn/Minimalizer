# Local private HTTPS current retry evidence — 2026-11-17

This is a source-free operational recheck against the adopted production
Worker. It records the failure path only; it does not promote the L04 bundle
or replace the owner iPhone acceptance receipt.

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

## Gate interpretation

This proves the current retry signal is present on the adopted Worker. It does
not prove a successful output for this recheck, SVG delivery, L04 formal PASS,
or current-commit iPhone acceptance. Existing successful replay and rollback
evidence remains bound to its recorded receipts and must not be silently
rebound to another commit.
