# Phase 2 — Analysis Foundation

Status: implementation

## Scope
Phase 2 establishes analyzer-independent Evidence production. It does not perform evidence fusion, scene understanding, semantic authority, geometry selection, or rendering.

## Definition of Done
- schema_version 1.0 canonical contracts exist for all Phase 1 data-model types
- absolute/normalized coordinate invariants are tested
- canonical JSON serialization is stable and deterministic
- AnalyzerAdapter emits only normalized Evidence records
- provenance records producer/model identity independently from canonical schemas
- at least two deterministic classical baseline evidence producers are available
- optional analyzer failure cannot corrupt canonical schema contracts
- ZeroBase tests require no network access or model download
- current Minimalizer production entry points do not import ZeroBase
- repository tests pass and Phase 2 state is recorded in Canonical HANDOFF

## Baselines
1. OpenCVContourAdapter: external contour evidence with deterministic ordering.
2. SLICRegionAdapter: deterministic superpixel-region evidence normalized into the same Evidence contract.

Heavy analyzers (MediaPipe, rembg, SAM) remain deferred until a later measured integration step. They are not required to close Phase 2.


## 2026-10-06 PB2 backport

Phase 2 has received a backward-compatible observer-only evidence expansion after SA7 closeout.

New structured source evidence:
- disconnected component identity;
- layer relation evidence (OVERLAP / TOUCHING / DISJOINT);
- optional canonical-z observation provenance;
- explicit observed/advisor/promoted authority provenance.

The original Phase 2 scope remains unchanged: this layer still does not fuse evidence, choose semantic authority, select geometry, or render.

PB2 evidence intentionally does not expose the production `geometry.bbox` contract and therefore fails closed if accidentally routed to the current `EvidenceFusion`.

Canonical record:
`PB2_SA2_EVIDENCE_ADAPTER_BACKPORT_20261006.md`
