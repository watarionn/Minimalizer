# ZeroBase Phase 11 — Production Pipeline

Status: CLOSED candidate

## Production contract
Phase 11 wires normalized Evidence through EvidenceFusion, RegionReconstructor,
ImportanceEngine, PaletteMaterialEngine, PrimitiveGenerator, GeometryOptimizer,
SemanticComposer, and deterministic SvgRenderer.

The pipeline persists canonical stage artifacts:
1. normalized Evidence
2. fused Scene
3. reconstructed Scene
4. importance Scene
5. palette/material Scene
6. primitive candidates
7. optimization result
8. VectorScene
9. canonical SVG
plus a versioned manifest.

Replay starts from saved normalized Evidence and must reproduce the same optimization,
VectorScene, and SVG without analyzer execution or network access.

## Runtime placement
The deterministic baseline stays in-process with the application/runtime boundary.
A measured synthetic 512x512 RGB baseline on YWSHTMR produced 64 SLIC Evidence records:
SLIC ~139.37 ms; downstream ProductionPipeline ~16.70 ms; 64 primitives.
This measurement is diagnostic, not a production SLA.

Optional heavy analyzers remain out-of-core capabilities behind AnalyzerAdapter.
No GPU/local-worker requirement is promoted by Phase 11. A heavy analyzer may later run
in a separate worker only when measured latency, memory, deployment, or license constraints
justify it. Its output must still terminate at normalized Evidence.

## Material evidence
SLIC normalization now records deterministic mean RGB base_color per region.
Illumination remains separate/disposable by the Phase 6 contract.
Missing base_color fails closed by default; neutral gray fallback exists only behind an
explicit ProductionPipelinePolicy switch.

## Migration boundary
ZeroBase remains isolated under minimalizer_zerobase/.
Phase 11 does not import ZeroBase from app/, web/, or minimalize_engine/.
Current Minimalizer 2.0 production behavior is unchanged.

## Verification
- ZeroBase suite: 58 passed
- real SLIC Evidence -> ProductionPipeline -> SVG: PASS
- deterministic input-order replay: PASS
- saved-artifact replay equality: PASS
- missing material evidence fail-closed: PASS
- source Evidence immutability: PASS
- deterministic SVG serialization: PASS
- production import boundary: PASS required before closure
- git diff --check: PASS required before closure

## Phase 12 entry
Phase 12 owns the Final Quality Gate. It must validate production-boundary isolation,
artifact replay, deterministic output, release/license notices, and available Approved-78
replay/calibration evidence. Phase 11 does not invent Approved-78 measurements where
canonical Scene/candidate pairs are still absent.
