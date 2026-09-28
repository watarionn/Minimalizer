# Artifact Contract Foundation Phase 1

Status: CLOSED / PASS

Date: 2026-09-28

This is a cross-cutting ZeroBase 2nd Cycle foundation change. It does not replace or reorder the canonical Phase map. Phase 7 Major Mass Reconstruction remains the next visual algorithm phase.

## Goal

Formalize the existing Stage Artifact Contract into reusable run/artifact provenance types without changing visible output.

The foundation makes the non-generative policy machine-checkable instead of relying only on documentation.

## Implemented contracts

New package:

`minimalizer_zerobase/artifact_contract/`

Core models:

- `ArtifactOrigin`
- `ArtifactParentRef`
- `ArtifactRecord`
- `ArtifactManifest`
- `RunManifest`
- `RunPolicy`
- `PartState`
- `SemanticPartState`


Artifact origin values are:

- `source_pixel`
- `analytical`
- `geometric_derivation`
- `semantic_metadata`
- `synthesized`
- `unknown`

Typed part states are:

- `present`
- `absent_by_design`
- `not_visible_in_source`
- `not_detected`
- `ambiguous`
- `qa_dropped`

`not_visible_in_source` is explicitly distinct from missing data and must not cause hidden-region synthesis.

## Observed-only gate

`ProvenancePolicyGate` validates:

- unique artifact IDs
- parent existence
- parent SHA-256 binding
- acyclic provenance lineage
- visible-origin restrictions
- source-pixel ancestry for every visible artifact
- rejection of any synthesized/unknown official artifact
- rejection of synthesized/unknown visible lineage
- run policy rejection when generative visible pixels, inpainting, or img2img are enabled


## Persistence

`write_contract_bundle()` deterministically writes:

- `run.json`
- `artifacts.json`

Artifacts are sorted by artifact ID before serialization.

The same manifest and artifact set produce byte-identical JSON and identical SHA-256 values.

## Canonical serialization

`CanonicalModel` now serializes Python `Enum` values to their stable string values.

This is backward-compatible with existing dataclass/list/dict serialization and does not modify render logic.

## Safety boundary

No existing Phase 3-6 writer or production render path imports the new artifact package yet.

Therefore this phase is intentionally zero-visible-change:

- no Minimalizer 2.0 route changes
- no ZeroBase rendering changes
- no analyzer authority changes
- no production switch
- no generated or inpainted pixels


## Tests

Focused contract tests cover:

- canonical enum serialization
- typed absence invariants
- valid observed-only lineage
- synthesized/unknown visible artifact rejection
- visible artifacts without source-pixel ancestry
- missing parent detection
- parent hash mismatch detection
- cycle detection
- forbidden run policy detection
- duplicate artifact manifest IDs
- deterministic contract persistence

Focused result: 12 passed.

Full `tests/zerobase` result: 110 passed.

Existing local merge-readiness: PASS. Stable/Web regressions 131 passed, Phase 16 corpus gate PASS, and real-server smoke PASS.

## Next integration step

Backfill the existing Phase 3-6 Stage Artifact Contract into the common artifact graph without changing their current files or rendering.

The intended bridge is:

`stage.json -> ArtifactRecord set -> artifacts.json/run.json -> ProvenancePolicyGate`

Only after that bridge is stable should Phase 7 masses become first-class lineage nodes.
