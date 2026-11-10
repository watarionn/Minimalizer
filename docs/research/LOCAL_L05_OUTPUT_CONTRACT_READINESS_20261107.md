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

The source-free `tools/research/local_l05_owner_run_receipt.py` validator and
`tests/test_local_l05_owner_run_receipt.py` define the readback contract for
that future owner run. It requires private HTTPS, verified owner/origin/Tailnet
identity, `/health` readiness, both PNG success routes, 415/429/503 failure
paths, Retry-After readback, and input/output file hashes. It deliberately
returns `L05_formal=HOLD` and `production_release=NO_GO`; it cannot substitute
for the real request or physical-device acceptance.

## 2026-11-10 read-only reconciliation

The focused B source QA was rerun from the current Draft #451 head
`c593b46c53c28127b08d74d2ce733045495b5577`:

```text
tests/test_local_worker.py
tests/test_local_l04_source_stage8_svg_triple_gate.py
tests/test_local_l05_owner_run_receipt.py
tests/test_local_l07_pwa_privacy_audit.py
tests/test_minimalizer_page_split.py
64 passed in 4.14s
```

The static L07 audit returned `STATIC_SW_PRIVACY_CONTRACT_PASS` and
`STATIC_LOCAL_ROUTE_ISOLATED`. It still returned
`L07_actual_live_iphone=NOT_TESTED` and `L08_release=NOT_APPROVED`. No private
source, output artifact, production asset, or worker configuration was changed
by this reconciliation. B remains QA-ready but not formally released.
