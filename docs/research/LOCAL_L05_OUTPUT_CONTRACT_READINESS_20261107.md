# Local L05 output-contract readiness (2026-11-07)

**Read-only integration QA: source-level FastAPI/TestClient paths pass; private HTTPS, real PC/iPhone and production deployment remain NOT TESTED. L05: HOLD; production: NO_GO.**

The current LocalWorker contract was exercised through the existing
`tests/test_local_worker.py` suite, not only by inspecting source text. The
focused run passed **16/16**. It covered:

- `/health` cold-runtime response and readiness fields;
- private/local Origin acceptance and untrusted/public Origin rejection;
- private-network preflight;
- `/api/v2/minimalize` PNG body/header contract with a controlled exporter;
- `/api/zerobase2/minimalize` PNG route/provenance/input digest headers;
- ZeroBase2 authorization fail-closed response;
- private Tailnet owner-login gate, forwarded-identity rejection and
  unconfigured-owner rejection;
- simultaneous-job `429` behavior for both output routes; and
- Local PWA shell serving without browser fallback.

The inspected route is PNG-only for standard LocalWorker output. The existing
browser Color Strip SVG path must not be treated as official Local L04 Stage8
SVG evidence. No private HTTPS request, Tailscale data-plane observation,
Safari/iPhone save, physical saved-file hash, Service Worker browser upgrade,
or production response was exercised in this run. The actual three-artifact
L04 gate is recorded separately in
`LOCAL_L04_SOURCE_STAGE8_SVG_TRIPLE_GATE_20261107.md`.

No source image, NPZ, mask, coordinate, comparison image, secret, Public/C08
asset, Golden asset, or production state was changed. L05 cannot be promoted
from this TestClient result; the remaining gate is an owner-authorized private
HTTPS PC/iPhone run with PNG input/output and failure-path readback.
