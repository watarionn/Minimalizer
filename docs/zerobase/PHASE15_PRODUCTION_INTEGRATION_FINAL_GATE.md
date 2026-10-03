# Phase 15 Production Integration & Final Gate

Status: READY FOR DEPLOYMENT SMOKE (not MIGRATION CLOSED)

## Completed

- Phase 14 closure authorizes Phase 15.
- Development and production-run outputs are pixel-identical.
- Raden SHA256: b737a7df3202fd0f731f28ccd76c03b2a15621af3807617327f8a9d2160b7215.
- ZeroBase2 Local Worker endpoint returns HTTP 200 and route=zerobase2.
- Profile is conservative, shape count is 14, rollback is available.
- Web UI opt-in flag: ?engine=zerobase2&localWorker=1.
- Default production route remains unchanged without the flag.
- Minimalizer 2.0 rollback path is retained.

## Runtime contract

Local Worker production runtime is Python 3.11 under .venv311.
The previous setup script did not install the full requirements-local-worker.txt, and the existing .venv was Python 3.14. Phase 15 exposed both problems. Setup/start scripts now target the Python 3.11 worker runtime and setup installs the full requirements file.

## Final gate

Do not mark MIGRATION CLOSED until the deployed ShinFree UI is exercised in real Chrome with the ZeroBase2 feature flag and response evidence proves X-Minimalizer-Route: zerobase2. Browser Fallback v12, Minimalizer 2.0, and silent fallback never count as ZeroBase2 success.

Required evidence: real-browser standard-button smoke, ZeroBase2 route evidence, visible output, rollback available, and Phase 15 gate updated to migration_closed=true.

## Evidence

- artifacts/phase15_production/15_production_gate.json
- artifacts/phase15_production/15_production_compare_board.png
- artifacts/phase15_production/15_zerobase2_api_headers_311.txt
- artifacts/phase15_production/15_zerobase2_api_output_311.png
