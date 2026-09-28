# ZeroBase 2nd Cycle Phase 5 — Structural Layout Graph

Status: **CLOSED / PASS**

## Objective

Phase 5 consumes the immutable Phase 4 semantic part masks and connects those parts as an explicit person-structure graph. It does not relabel, redraw, dilate, erode, or otherwise modify any Phase 4 mask.

The graph records:

- deterministic part anchors in pixel and normalized coordinates
- attachment, spatial, containment, overlap, surrounding, and occlusion relations
- confidence, evidence references, and measured mask geometry for every relation
- validation for isolated major parts, arm attachment, accessory attachment, and front/behind cycles

## Implementation

The implementation is split into pure graph construction, artifact rendering/persistence, and CLI orchestration.

- `minimalizer_zerobase/structure/graph.py`
  - builds centroid and nearest-boundary anchors
  - derives relations only from Phase 4 masks and Phase 4 accessory evidence
  - keeps front/behind relations as a directed acyclic graph
  - fails closed when a present major accessory has no supported attachment
- `minimalizer_zerobase/structure/artifacts.py`
  - writes the canonical graph JSON, mandatory overlay/preview, metrics, and bound stage manifest
  - draws fixed part-boundary, anchor, and relation colors for all cases
- `scripts/zerobase2_phase5_structure.py`
  - verifies the source and every Phase 4 part-mask SHA before graph construction
  - reads Phase 4 only and writes exclusively to `phase_05`

The relation policy is semantic-first rather than distance-only. In particular:

- vivid torso accents attach to `torso`
- `held-linear` evidence selects the nearest arm candidate before torso/head candidates
- face is contained by head when Phase 4 overlap supports it
- hair surrounds and overlaps the head region and remains behind the visible face according to the Phase 4 display contract
- major clothing and accessories remain in front of their attachment targets

## Artifact contract

Runtime artifacts:

`artifacts/zerobase2/<case_id>/phase_05/`

Each case contains:

- `05_structure_graph.json`
- `05_structure_graph_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

Persistent diagnostic snapshots:

`docs/zerobase/diagnostics/phase05/<case_id>/`

`stage.json` binds the canonical source SHA, all Phase 4 part-mask SHAs, Phase 4 metrics/stage SHAs, config SHA, analyzer provenance, coordinate space, determinism policy, graph payload, and output SHAs.

## Phase 4 immutability

Both Diagnostic-2 runs verified all 11 Phase 4 part-mask files against the SHAs recorded by their Phase 4 stage manifests before loading them. Phase 5 makes boolean copies for calculation and has no Phase 4 write path.

Verified Phase 4 inputs: **22/22 masks SHA-bound**.

## Diagnostic-2 results

### Hyakuto Kyoko

- Canonical source SHA-256: `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`
- Present parts: 10
- Anchors: 24
- Relations: 16
- Isolated major parts: 0
- Missing arm attachments: 0
- Missing accessory attachments: 0
- Occlusion cycles: 0
- Accessory attachment: vivid accent → torso
- Visual QA: **PASS**

The overlay keeps the face inside the head structure, hair around the face/head, the head above the torso, both arms attached to the torso, lower body attached below it, and the green tie/accent attached in front of the torso. All anchors and relation arrows are readable on the aligned character view.

The canonical Kyoko source file was not present in the checkout at closure time. The renderer therefore used the SHA-bound Phase 3 subject overlay as the diagnostic visual source; it preserves original subject pixels while dimming background pixels. The canonical source SHA remains inherited from and checked against Phase 3/4.

### Juufuutei Raden

- Canonical source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Present parts: 10
- Anchors: 24
- Relations: 16
- Isolated major parts: 0
- Missing arm attachments: 0
- Missing accessory attachments: 0
- Occlusion cycles: 0
- Accessory attachment: held linear object → right arm
- Visual QA: **PASS**

The first distance-only diagnostic attached the held-linear mask to the broad structural head mask. Visual review rejected that semantic result. The final policy uses the Phase 4 `held-linear` evidence to select an arm candidate, then chooses the nearer arm. The final overlay connects the rod to Raden's right arm while retaining the corrected face, long hair, torso, and both sleeves from Phase 4.

## Determinism

The identical Diagnostic-2 command was executed twice after the final relation policy. The graph JSON, overlay, preview, metrics, and stage manifest were byte-identical for both cases.

Kyoko:

- graph: `55aef2ca424db94eb82b20a2413599cc59fceea2a3534b6e4e1182e0ed61706a`
- overlay / preview: `de021b8bbe90bad48fce3b171533a1c089a471d027adb43a604b4bc8818d8a7f`
- metrics: `1f7301d66cad3c79afa206999c8f97501554b88d3b4100fa09044cce2796c8e1`
- stage: `c24301e76e92fb31ebf5e8ebba19664807273185e6612b3f622b14e9dd7ac4b3`

Raden:

- graph: `c6b76f299e0df8a8835d87c39e0fb9c6a6345498276f5b48324a03242e4f3962`
- overlay / preview: `318e17e977a16935d29c53705c0812239959be44a661d9075d5780f7af15a17a`
- metrics: `1f7301d66cad3c79afa206999c8f97501554b88d3b4100fa09044cce2796c8e1`
- stage: `9f674b21ea3114d7d36a329927ee5db0a419e3342e0d06880882220d6db0a874`

## Regression

- Phase 5 focused tests: **6 passed**
- Full ZeroBase suite: **83 passed**
- Diagnostic-2 visual QA: **2/2 PASS**
- Deterministic mandatory artifact rerun: **10/10 SHA MATCH**
- `git diff --check`: **PASS**

## Gate decision

Phase 5 is **CLOSED / PASS** for Diagnostic-2.

The next canonical phase is **Phase 6: Region-to-Part Binding**. Production remains Minimalizer 2.0; ZeroBase remains a development/comparison path and is not switched into production.
