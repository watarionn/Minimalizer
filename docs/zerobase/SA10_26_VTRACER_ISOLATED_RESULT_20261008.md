# SA10.26 VTracer isolated transaction result - 2026-10-08

VTracer 0.6.15 was moved behind a subprocess boundary after the in-process native extension caused a Windows access violation. The parent Minimalizer process no longer imports VTracer. Child crash, timeout, or nonzero exit returns explicit fallback_noop.

## Real execution

Canonical venv isolated worker successfully generated SVG for a synthetic mask and for the canonical GC001 source alpha mask. GC001 worker exit_code=0 and emitted 1635-byte SVG. The rasterized foreground candidate was clipped to the immutable source mask.

GC001 source-bound evidence: IoU=1.0, connected components 1->1, material_topology_preserved=true, but boundary_recall=0.517857, below the existing 0.90 hard threshold. Therefore the VTracer candidate is rejected/rolled back. No threshold was changed and no production promotion occurs.

Because the first required real regression case already fails an authoritative hard gate, the untouched fresh holdout is intentionally not exposed/tuned in this tranche. This preserves it for the next external implementation benchmark.

## Verification

- focused SA10.19/26: 9 passed
- full tests/zerobase: 906 passed
- compileall: PASS
- git diff --check: PASS
- VTracer remains optional and isolated
- no generated pixels; candidate is source-clipped

## Decision

VTracer is retained as an isolated experimental backend, but is REJECTED as a production-authoritative candidate generator under the current deterministic settings. Next candidate: AnimeSeg semantic observer, with the untouched holdout still sealed until GC001 observer integration is healthy.
