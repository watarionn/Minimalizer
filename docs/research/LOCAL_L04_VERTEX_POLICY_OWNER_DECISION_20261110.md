# Local L04 geometry policy decision (2026-11-10)

**Decision: Local L04 does not enforce a vertex-count cap.**

This source-free decision applies only to Lane B's Local L04 representation and
delivery checks. It does not change Lane A image quality, Phase4/Phase5,
Public/C08, Golden assets, signed originals, or production state.

## Adopted policy

- Historical case values such as `1887` and `1412` are removed from the active
  Local L04 acceptance rule.
- Original Stage8 and expanded-SVG vertex counts remain observable diagnostics,
  not pass/fail criteria.
- L04 checks source/Stage8/SVG SHA linkage, safe SVG structure, source-owner
  exactness, protected-face/arm exactness, and source-silhouette equality.
- A resource guard may be added only after measurement on the actual Local
  runtime. Its inputs are bytes, SVG element count, parse/render time, memory,
  and timeout; it must not be inferred from a historical vertex value.
- A resource failure must be explicit and must not silently rewrite the SVG or
  switch to a different-quality fallback.

## Current candidate readback

The source-preserving private candidate records:

| Case | Expanded SVG vertices | Owner mismatch | Protected mismatch | Silhouette XOR |
|---|---:|---:|---:|---:|
| H06 | 72,201 | 0 | 0 | 0 |
| H08 | 56,249 | 0 | 0 | 0 |

These values are observations only. They do not constitute production approval.

## Remaining B gates

1. Read back the exact private source/Stage8/SVG triple and its receipt.
2. Run the actual Local runtime measurement and record bytes, parse/render time,
   memory, and timeout behavior.
3. Verify Chromium desktop and Safari/PWA behavior for the exact output.
4. Verify generation-pinned Service Worker update, offline behavior, rollback,
   and private-HTTPS failure handling.
5. Keep production release unauthorized until the owner-side production and
   physical-device acceptance is read back.

No code path may reintroduce `1887` or `1412` as an active Local L04 cap.

## Independence boundary

This decision concerns only Lane B's representation budget. It does not relax
Lane A's observer capability gate, semantic owner requirements, Phase4/Phase5,
human visual review, or the handoff requirement that A supply a completed
Stage8/SVG set.
