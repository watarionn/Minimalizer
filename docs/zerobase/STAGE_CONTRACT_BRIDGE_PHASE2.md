# Stage Contract Bridge Phase 2

Status: CLOSED / PASS

Date: 2026-09-28

This is a cross-cutting ZeroBase 2nd Cycle provenance integration. It does not reorder the canonical visual Phase map. Phase 7 Major Mass Reconstruction remains the next visual algorithm phase.

## Goal

Bridge the already-closed Phase 3-6 Stage Artifact Contract into the common Artifact Contract Foundation without changing any existing phase output or visible render.

Canonical bridge:

`stage.json -> verified ArtifactRecord DAG -> run.json / artifacts.json -> ProvenancePolicyGate`

## Implementation

Added:

- `minimalizer_zerobase/artifact_contract/bridge.py`
- `tools/bridge_zerobase_stage_contracts.py`
- `tests/zerobase/test_stage_contract_bridge.py`

The bridge is read-only with respect to `phase_03` through `phase_06`.

Generated provenance files are written to a sibling directory:

`artifacts/zerobase2/<case_id>/artifact_contract/`

Files:

- `run.json`
- `artifacts.json`
- `provenance_gate.json`


## Verification boundary

The bridge fails closed unless all of the following are true:

- Phase 3, 4, 5, and 6 `stage.json` files exist.
- Each stage declares its expected phase number and required contract fields.
- Each stage config re-hashes to its declared `config_sha256`.
- Every declared output exists on disk and matches its declared SHA-256.
- Every declared upstream input resolves to an already verified artifact.
- Every upstream input SHA matches the resolved artifact SHA.
- Direct source/visual-source inputs resolve to the canonical source or a verified prior artifact.
- The actual source file SHA matches the Phase 3 canonical source SHA.
- The actual source dimensions match the Phase 3 canonical source dimensions.
- All stage source SHA/dimensions remain consistent from Phase 3 through Phase 6.
- No stage artifact path contains an absolute path or path traversal.
- The final common `ProvenancePolicyGate` passes.

The bridge never invents a missing parent and never substitutes a same-looking artifact when a declared SHA cannot be resolved.

## Artifact mapping

Canonical artifact IDs are stable:

- `source`
- `phase03:<relative-path>`
- `phase04:<relative-path>`
- `phase05:<relative-path>`
- `phase06:<relative-path>`

Each `stage.json` itself is also a first-class artifact, for example:

`phase04:stage.json`

Output origin mapping:

- JSON structural/semantic outputs: `semantic_metadata`
- PNG masks/maps/overlays/previews: `analytical`
- Source image: `source_pixel`

Current Phase 3-6 diagnostic images are not marked as final visible render authority.


## Determinism

The verified source filesystem location is intentionally excluded from canonical manifest content.

Therefore identical source bytes plus identical Stage Artifact Contracts produce identical `run.json` and `artifacts.json` even when the verification source is read from a different local path.

The run-level config SHA is the canonical SHA of the Phase 3-6 config SHA map.

## Diagnostic-2 real-data validation

### Hyakuto-Kyoko

- Artifact count: 34
- Provenance Gate: PASS
- `run.json` SHA-256:
  `7025329fae3c818316c5da1d4d259a012e1fcda762f14016c88ed327d2587cd7`
- `artifacts.json` SHA-256:
  `aa94254f439202595f5b0c428b5ed0ca3b605cafed31612f82606460c936d652`
- `provenance_gate.json` SHA-256:
  `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

### Juufuutei-Raden

- Artifact count: 34
- Provenance Gate: PASS
- `run.json` SHA-256:
  `1da078ef6618f87bad501f4b935ef49014fdbc50b7147fc6baf303400122592d`
- `artifacts.json` SHA-256:
  `b5af87b476e3a2c0be3b6e2421df96241ea4a378647f110aebc585c7fbd4ce6d`
- `provenance_gate.json` SHA-256:
  `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

Raden was verified from two distinct local source paths containing identical bytes. Both produced exactly the same run/artifact/gate SHA values.


## Negative fixtures

Focused bridge tests prove rejection of:

- modified declared output
- upstream input SHA mismatch
- source replacement
- config mutation without matching config SHA
- unsafe/path-traversal or absolute output declaration

The existing Artifact Contract Foundation tests continue to cover forbidden generated/unknown origins, parent hash mismatch, missing parents, graph cycles, typed absence, and deterministic persistence.

Focused Artifact Contract + Bridge result: 20 passed.

Full `tests/zerobase` result: 118 passed.

Existing local merge-readiness: PASS.

- Stable/Web regressions: 131 passed
- Phase 16 corpus gate: PASS
- real-server smoke: PASS
- final marker: `LOCAL_MERGE_VALIDATION_PASS`

## Safety boundary

Unchanged:

- Minimalizer 2.0 production route
- Phase 3-6 artifact bytes
- Phase 3-6 visual previews
- analyzer authority
- render authority
- production fallback
- canonical visual Phase order

No generated, inpainted, or hidden-region-completed pixels are introduced.

## Next architecture step

Phase 7 Major Mass artifacts can now be attached to a verified Phase 3-6 provenance chain instead of starting a new unbound lineage.

The next integration should extend the common bridge contract to Phase 7 outputs without changing the Phase 7 mass algorithm itself.
