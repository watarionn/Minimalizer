# SA7.15 Region-Conditioned Structural Verifier — 2026-10-05

Status: SAFETY FILTER ADOPTED / PROMOTION AUTHORITY NO-GO

## Role
SA7.15 is explicitly dependent on SA7.9 region proposals. It is not an independent observer role and can never satisfy SA7.6 independence by itself.

It verifies local paired/frame topology inside a supplied candidate at enlarged local scale and returns only the source candidate mask. It never synthesizes lens geometry.

## Synthetic contract
5 PASS:
- glasses-like paired closed structure + bridge passes,
- eye dots fail,
- single loop fails,
- oversized candidate fails,
- verifier cannot invent geometry.

## Non-target evaluation v1
Initial real-image run:
- Sopia positive: reject
- Flare positive: reject
- AZKi negative: ACCEPT 0.60657 (bad)
- Gura/Fauna/Mumei negatives: reject

Before GC001 evaluation, candidate-mask overlap >= 0.72 was added to prevent unrelated structures inside a coarse bbox from passing.

After safety fix:
- Sopia positive: reject
- Flare positive: reject
- AZKi negative: reject
- Gura negative: reject
- Fauna negative: reject
- Mumei negative: reject

The verifier therefore improves false-positive suppression but has zero positive recall on these thumbnail references.

## Decision
Adopt only as a conservative false-positive filter. Do not use as semantic promotion authority. Do not run GC001 to tune around the non-target failure. Renderer remains disconnected.

## Implementation incident
A programmatic source replacement accidentally wrote literal backslash-n sequences into Python and caused SyntaxError during test collection. No main-branch impact. It was immediately fixed by fetching the full file, normalizing the escaped newlines, and rerunning focused tests.

Cause: unsafe string replacement for multiline Python source.
Impact: feature branch temporarily failed import; no production/main change.
Fix: normalize exact source and rerun tests.
Prevention: avoid escaped multiline replacement; fetch/read changed source and run import/focused tests immediately after programmatic edits.

This is a recurrence of the previously known escaped-newline source-edit failure and should remain covered by the project mistake log.

## Next
SA7.16 should stop trying to infer tiny eyewear solely from thumbnail raster topology. Investigate a frozen external/local eyewear-specific detector or higher-resolution source evidence, evaluated on a larger non-target corpus before GC001.
