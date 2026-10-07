# SA10.23 Real GC001 Structural Transaction — 2026-10-07

Status: CLOSED / PRODUCTION PROMOTION BLOCKED

## Canonical source

Drive `GC001_source.png` (file id `1LxHHizN1nC9JVpbHegqMtO38O6xWwjpj`) was fetched and byte-matched to the existing local canonical `C:\Work\Temp\macro-gc001\GC001.png`.

SHA-256: `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e`.

A clean reviewed-sa10 Phase 3-12 run completed at `C:\Work\Temp\sa1023-gc001-clean3\GC001_source`; Phase 12 provenance gate completed with 76 artifacts. Phase 13 provenance passed with 81 artifacts. Phase 14 provenance passed with 86 artifacts.

## Generic runtime repair

The real run exposed an OpenCV HoughLinesP shape assumption in `_detect_peripheral_linear_accessory`: indexing `lines[:, 0]` collapses a flat/single-line return to scalar `numpy.int32`. Production code now normalizes any coordinate-compatible Hough output to `N x 4`. This is generic and has no GC001 constants or branches. Regression covers flat single-line and nested OpenCV variants.

## Real Phase 14 result

The real candidate is NOT eligible for BEST / production promotion.

- Phase 14: FAIL
- machine_pass: false
- silhouette preservation IoU: 0.98948 (ordinary silhouette metric passes)
- source outer-boundary recall: 0.6235384320490703, required >= 0.90: FAIL
- source-visible left arm recall: 0.9933701657458563: PASS
- source-visible right arm recall: 0.92368177613321: PASS
- face bbox IoU: 0.8684093929995569: PASS
- head bbox IoU: 1.0: PASS
- structural topology: FAIL
- fragmentation penalty: 0.05263157894736842 <= 0.20: PASS
- source-shape evidence: PASS, observer-only

Topology mismatches include left-arm component/Euler changes, right-arm Euler/hole changes, and multiple source-part/union topology changes. These hard failures are not overridden by the high aggregate silhouette IoU or observer evidence.

This closes the SA10.18 real-GC001 evidence gap: the malformed structural candidate cannot be promoted as BEST under the current hard-gate chain.

## Verification

- Phase 4 focused regression after generic Hough fix: 18 passed.
- SA10.22 focused regression remains 5 passed.
- Full ZeroBase regression and compile/diff checks are required before commit.

## Next

SA10.24 should repair the candidate-generation side of the source-boundary/topology failures generically. Do not weaken the 0.90 outer-boundary gate, topology equality, source anatomy, or fragmentation 0.20 threshold. The objective is to produce a candidate that passes the existing gates, not to recalibrate the gates around GC001.
