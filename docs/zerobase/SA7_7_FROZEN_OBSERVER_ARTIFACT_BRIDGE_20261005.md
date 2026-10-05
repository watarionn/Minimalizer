# SA7.7 Frozen Observer Artifact Reuse Bridge — 2026-10-05

Status: BRIDGE PASS / CANONICAL ARTIFACT GAP CONFIRMED / GC001 HOLD

## Goal

Reuse preserved observer evidence without rerunning or reinstalling heavyweight models, while preserving provenance and refusing to reconstruct masks from aggregate summaries.

## Canonical artifact audit

GitHub records the blind observer artifact:

- name: `GBLIND_HOLOMEN_20261005_frozen_observer_run.zip`
- SHA-256: `de498aa0769c7aa48665d93dc4b603d69123247d69e3a48fa514ad942ea14892`
- recorded preservation target: Google Drive / My Drive
- expected contents: full NPZ evidence, contact sheet, rembg masks, report, input manifest

A direct Google Drive search for the exact filename, `GBLIND_HOLOMEN`, and `frozen_observer_run` returned no artifact. The current Minimalizer Drive hierarchy was also inspected; the recorded ZIP was not present there.

Therefore the repository summary is evidence that the run occurred, but it is not enough to reconstruct spatial masks. The bridge must not synthesize bbox/masks from aggregate coverage values.

## Implementation

Added `semantic_abstraction/frozen_observer_bridge.py`.

The bridge accepts only records with:

- eyewear semantic label or explicit alias,
- confidence in [0,1],
- producer and model provenance,
- valid source-coordinate geometry (mask or bbox),
- supported observer role: region or feature_local.

It rejects:

- aggregate summaries without geometry,
- missing provenance,
- unrelated semantic labels,
- malformed/out-of-bounds geometry,
- undersized evidence.

Bound artifacts convert directly into SA7.6 `EyewearObserverEvidence` without changing confidence or semantic role.

## Verification

- focused SA7.5 + SA7.6 + SA7.7: 17 PASS
- full ZeroBase: 536 PASS
- git diff --check: PASS
- deterministic order-invariant binding verified

## GC001 decision

No frozen GC001 eyewear artifact with reusable spatial evidence was found. GC001 therefore remains HOLD.

No manual bbox, Golden-derived geometry, aggregate-to-mask reconstruction, threshold relaxation, model reinstall, or renderer change was performed.

## Preservation incident

The historical record says the blind ZIP was preserved to Drive, but the artifact is not discoverable at the recorded location now. This is a preservation/indexing gap. Future observer runs must store a canonical Drive file ID and exact parent folder in the repository record, then verify the file by ID after upload.

## Next: SA7.8 Observer Artifact Recovery / Reproduction Gate

1. search known canonical project folders and historical handoffs for the exact ZIP/file ID,
2. if found, verify SHA-256 before use,
3. if not found, mark the historical artifact LOST/UNRESOLVED rather than pretending it is reusable,
4. inspect whether existing model caches can be recovered without duplicate installation,
5. only if recovery is impossible and rerun is justified, perform one shared observer-runtime restoration,
6. run non-GC001 fixture/holdout first,
7. then GC001 untouched observer inference,
8. feed raw evidence through SA7.7 -> SA7.6,
9. renderer remains disconnected until semantic evidence passes review.
