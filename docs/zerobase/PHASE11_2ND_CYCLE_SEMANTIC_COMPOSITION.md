# ZeroBase 2nd Cycle Phase 11 — Semantic Composition

Status: **CLOSED / PASS**

Phase 11 is implemented, locally verified, and independently re-reviewed by Rinka. Phase 12 has not started, and Minimalizer 2.0 remains the production standard.

## Scope

Phase 11 consumes the immutable, SHA-bound outputs of:

- Phase 5 structural graph
- Phase 10 selected primitives, semantic owners, Phase 8 actions, and Phase 9 palette assignments

It emits a deterministic composed vector scene and two stage-visible raster views. It does not change geometry, semantic ownership, omission decisions, or palette assignments.

## Depth authority

- Only Phase 5 `in_front_of` and `behind` relations create semantic depth edges.
- `inside`, `overlaps`, `surrounds`, attachment, and spatial relations never create z-order.
- Unresolved overlapping part pairs remain explicit in `11_composition.json`.
- Whole-hair / face depth remains unresolved unless Phase 5 supplies an explicit depth relation.
- The raster preview uses a per-pixel signature of the actual Phase 10 primitive masks and Phase 9 palette colors only where the explicit depth graph is silent. This tie-break is deterministic rendering machinery, not a semantic depth claim.
- Region ID and mass ID ordering are forbidden as drawing authority. An identifier can break a final serialization tie only after masks and colors are visually identical, where order cannot change the raster.

## Implementation

- Composer and primitive rasterizer: `minimalizer_zerobase/composition/semantic.py`
- Deterministic renderers and artifact writer: `minimalizer_zerobase/composition/artifacts.py`
- Public exports: `minimalizer_zerobase/composition/__init__.py`
- CLI: `tools/run_zerobase_phase11.py`
- Stage Contract Bridge: verified chain extended through `max_phase=11`
- Focused tests: `tests/zerobase/test_semantic_composer.py`
- Bridge tests: `tests/zerobase/test_stage_contract_bridge.py`

### Independent review correction

Rinka's first independent review found that the original part key used the union-mask digest and palette-color set, then the semantic part name. Two unresolved parts could therefore have the same union mask and color set but different spatial color layouts, allowing the semantic name to change the visible overlap. The corrected v2 key retains the existing observable union-mask and color-set fields, then includes the complete per-pixel RGBA raster made from each actual primitive mask and palette color. The semantic part name appears only after those exact bytes. Equal keys before that final name therefore paint exactly the same color at every occupied pixel, so swapping them cannot change the final image. Equal-visual ready nodes are drained as one batch so the serialization-only name tie also cannot indirectly change when a visually different node is considered.

The regression fixture uses two distinct semantic parts with no explicit depth relation, identical union masks, and identical palette color sets, but opposite red/blue spatial layouts. Swapping both semantic names and upstream array order leaves the visible raster unchanged. Primitive ordering likewise places packed mask bytes and palette color before primitive family/identifier, leaving identifiers as serialization-only ties for visually identical primitives.

## Mandatory artifacts

Each case emits:

- `11_composition.json`
- `11_composed_minimal.png`
- `11_zorder_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

Canonical development artifacts:

- `artifacts/zerobase2/Hyakuto-Kyoko/phase_11/`
- `artifacts/zerobase2/Juufuutei-Raden/phase_11/`

Persistent diagnostic mirrors:

- `docs/zerobase/diagnostics/phase11/Hyakuto-Kyoko/`
- `docs/zerobase/diagnostics/phase11/Juufuutei-Raden/`

## Diagnostic-2

### Hyakuto Kyoko

- Source SHA-256: `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`
- Selected primitives: 158
- Explicit Phase 5 depth edges applied: 2
- Unresolved overlapping part pairs retained: 14
- Fully occluded critical parts: 0
- Geometry / owner / action / palette changes: 0 / 0 / 0 / 0
- Prune resurrection / generated or inpainted pixels: 0 / 0
- Provenance gate: PASS, 67 artifacts
- Visual QA: PASS. The Phase 10 head/hair, face, torso, arms, and green tie remain readable; composition introduces no new full occlusion or giant-block collapse.

### Juufuutei Raden

- Source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Selected primitives: 74
- Explicit Phase 5 depth edges applied: 2
- Unresolved overlapping part pairs retained: 16
- Fully occluded critical parts: 0
- Geometry / owner / action / palette changes: 0 / 0 / 0 / 0
- Prune resurrection / generated or inpainted pixels: 0 / 0
- Provenance gate: PASS, 67 artifacts
- Visual QA: PASS. Long hair, face, body/sleeves, arms, and held-object evidence remain distinguishable; composition introduces no new full occlusion or giant-block collapse.

The applied edges are limited to the explicit Phase 5 relations: major clothing in front of torso in both cases, plus Kyoko's accessory in front of torso or Raden's accessory in front of the right arm. The Phase 5 `face inside head` relation is retained as non-depth topology and is not promoted to z-order.

## Determinism

A separate local rerun matched all six mandatory artifact SHAs for both cases (6/6 + 6/6), including `stage.json`.

- Kyoko `11_composition.json`: `2323e54a1882c2534423308d02dbe84925462ce7f8f44a9bf13b7b8bc7c14743`
- Kyoko `11_composed_minimal.png`: `c700f23c13fa7feb2835efc0b001bc4580697bbb9d06c5041a2d7ab1671490cc`
- Kyoko `stage.json`: `c4fe9640bc94a05f316f257ab95ac992d8c933cf9b75571f3b767b98e4fe4660`
- Raden `11_composition.json`: `8a2fc4dcd8b3a2069d093a37dab4bc08a5915b146d36ee7fe6431a160d2b0ce2`
- Raden `11_composed_minimal.png`: `588296a6e893018d778dc08cbc26acacd3f7fdccfef7c1822cd78d2675bf2327`
- Raden `stage.json`: `b8b0482d320eaa87c59b8eb7e84d388b0509d0a02d6493754292f0df4c4a2ed2`

The corrected canonical render was compared pixel-for-pixel with the pre-correction diagnostic mirror. `11_composed_minimal.png`, `11_zorder_overlay.png`, and `preview.png` changed by **0 pixels** for both cases. Their SHA-256 values remain unchanged; only composition JSON, metrics, and stage metadata changed to record the v2 contract and validation flags.

## Tests

- Focused semantic composer + Stage Contract Bridge: **26 / 26 passed**
- Explicit `max_phase=11` bridge test: **PASS**
- Full ZeroBase suite: **173 / 173 passed**

The pytest cache emitted the existing Windows cache-path warning after passing runs; it did not affect test execution or results.

## Independent re-review and closure

Rinka independently re-reviewed the corrected v2 tie-break and confirmed that semantic identifiers do not have visible drawing authority. Focused Phase 11 plus Stage Contract Bridge tests passed 26/26, the full ZeroBase suite passed 173/173, and `git diff --check` reported no errors beyond the existing LF/CRLF warnings. For both Diagnostic-2 cases, all six mandatory artifacts matched between canonical and separate rerun outputs (6/6 each) and between canonical and diagnostic mirrors (6/6 each). Implicit, containment-derived, and other non-explicit depth edges were 0; fully occluded critical parts and generated/inpainted pixels were also 0. Rinka directly re-inspected the Kyoko and Raden images and recorded visual PASS. The corrected render retained a 0-pixel visible PNG difference from the pre-correction output in both cases.

Phase 11 is therefore **CLOSED / PASS**. Phase 12 has not started. This closure update includes no commit, push, merge, production route change, or deployment.
