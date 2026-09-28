# ZeroBase 2nd Cycle Phase 5 — Structural Layout Graph

Status: **CLOSED / PASS**

## Objective

Phase 5 consumes the immutable Phase 4 semantic part masks and connects those parts as an explicit person-structure graph. It does not relabel, redraw, dilate, erode, or otherwise modify any Phase 4 mask.

The graph records:

- deterministic part anchors in pixel and normalized coordinates
- attachment, spatial, containment, overlap, surrounding, and supported occlusion relations
- confidence, evidence references, and measured mask geometry for every relation
- validation for isolated major parts, arm/accessory attachment, required core relations, and front/behind cycles

## Implementation

The implementation is split into pure graph construction, artifact rendering/persistence, and CLI orchestration.

- `minimalizer_zerobase/structure/graph.py`
  - builds centroid and nearest-boundary anchors
  - derives relations only from Phase 4 masks and Phase 4 accessory evidence
  - keeps unsupported relations absent rather than forcing a semantic guess
  - fails closed when required core structure is missing
- `minimalizer_zerobase/structure/artifacts.py`
  - writes the canonical graph JSON, mandatory overlay/preview, metrics, and bound stage manifest
  - draws fixed part-boundary, anchor, and relation colors for all cases
- `scripts/zerobase2_phase5_structure.py`
  - verifies the source and every Phase 4 part-mask SHA before graph construction
  - reads Phase 4 only and writes exclusively to `phase_05`

## Review correction

The first Codex implementation inferred `hair behind face` for the whole hair mask from Phase 4 display priority.

Human review rejected that relation because bangs and rear hair can legitimately occupy opposite depth roles. Phase 5 now records only the supported `hair surrounds face` / `hair overlaps head` topology and leaves whole-hair face depth unresolved.

Front/behind is still allowed where evidence is strong enough, such as:

- major clothing in front of torso
- detected accessory in front of its attachment target

Hair/face depth must wait until later semantic masses split front hair and rear hair.

The review also strengthened validation. In addition to isolated-part / arm / accessory / cycle checks, a PASS now requires the relevant present parts to satisfy:

- head above torso
- face inside head
- neck attached to face
- neck attached to torso
- lower body attached to torso
- hair related to head or face via supported overlap/surrounding evidence

## Relation policy

The relation policy is semantic-first rather than distance-only.

- vivid torso accents attach to `torso`
- `held-linear` evidence selects the nearest arm candidate before torso/head candidates
- face is contained by head when Phase 4 overlap supports it
- hair surrounds face and overlaps the head region without forcing whole-hair z-order
- major clothing and accessories may be in front of their attachment targets when supported

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
- Visual source: canonical original source
- Present parts: 10
- Anchors: 24
- Relations: 15
- Isolated major parts: 0
- Missing arm attachments: 0
- Missing accessory attachments: 0
- Missing core relations: 0
- Occlusion cycles: 0
- Accessory attachment: vivid accent → torso
- Hair/face depth: unresolved by design
- Visual QA: **PASS**

The overlay keeps the face inside the head structure, hair around the face/head, the head above the torso, both arms attached to the torso, lower body attached below it, and the green tie/accent attached in front of the torso.

### Juufuutei Raden

- Canonical source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Visual source: canonical original source
- Present parts: 10
- Anchors: 24
- Relations: 15
- Isolated major parts: 0
- Missing arm attachments: 0
- Missing accessory attachments: 0
- Missing core relations: 0
- Occlusion cycles: 0
- Accessory attachment: held linear object → right arm
- Hair/face depth: unresolved by design
- Visual QA: **PASS**

The original distance-only diagnostic attached the held-linear mask to the broad structural head mask. Visual review rejected that semantic result. The final policy uses Phase 4 `held-linear` evidence to select an arm candidate, then chooses the nearer arm.

## Determinism

The identical Diagnostic-2 command was executed twice after the reviewed relation policy. The graph JSON, overlay, preview, metrics, and stage manifest were byte-identical for both cases.

Kyoko:

- graph: `1632ecc675e226365fd2b578fd35cf894492b4dcedb50d32a5a1893e831eda25`
- overlay / preview: `fd6b98c405d254fe35f8d1707052fd6855238a5778d3ed4b353453b659a3fc92`
- metrics: `a7f7c357710d48acd798b1dc738ca77dc0c04dcdc4f6afd1f74b7c3f7e37d5ea`
- stage: `15fd29588574410ee5771a2e6bdc11399f3cfb123bd3c2b8203ed337dbe1891f`

Raden:

- graph: `2fd327b826ad4838bcbaac25ea1e412fe641872b7d6267659c9c36cbffa63efe`
- overlay / preview: `47fb717755be9efa8231112495679dc55982eb4d1db9f8e2eb888d0a6c766ddb`
- metrics: `a7f7c357710d48acd798b1dc738ca77dc0c04dcdc4f6afd1f74b7c3f7e37d5ea`
- stage: `a2a7080e668da3bb6e68e47a188263aa3548c6a57d653c855ba33b75ab801ced`

## Regression

- Phase 5 focused tests: **8 passed**
- Full ZeroBase suite: **85 passed**
- Diagnostic-2 visual QA: **2/2 PASS**
- Deterministic mandatory artifact rerun: **10/10 SHA MATCH**
- Stable regression/Web set: **131 passed**
- Phase 16 corpus local gate: **PASS**
- Real-server local smoke: **PASS**
- `LOCAL_MERGE_VALIDATION_PASS`
- `git diff --check`: **PASS**

## Gate decision

Phase 5 is **CLOSED / PASS**.

The next canonical phase is **Phase 6: Region-to-Part Binding**.

Production remains Minimalizer 2.0. ZeroBase remains a development/comparison path and is not switched into production.
