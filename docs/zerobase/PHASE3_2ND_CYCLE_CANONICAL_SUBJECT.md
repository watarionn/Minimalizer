# ZeroBase 2nd Cycle Phase 3 — Canonical Subject Extraction

Status: **CLOSED / PASS**

## Objective

Phase 3 establishes one canonical foreground subject before any semantic-part or geometry work begins.
It must reject non-informative alpha, preserve evidence provenance, and emit mandatory stage images.

## Structural finding

The Diagnostic-2 PNG files contain alpha, but alpha is not a person cutout.
For both Kyoko and Raden, pixels with alpha >= 128 cover 99.68166089965398% of the 340x340 canvas.
The 1st Cycle rule "alpha exists => alpha is foreground" therefore treated almost the whole image as subject.

2nd Cycle now validates whether alpha is informative before using it.
Alpha is accepted only when its foreground ratio is between the configured subject bounds.
Nearly full-frame alpha is rejected and the fallback analysis provider is used.
## Canonical implementation

- Module: `minimalizer_zerobase/subject/extraction.py`
- Artifact writer: `minimalizer_zerobase/subject/artifacts.py`
- Runner: `scripts/zerobase2_phase3_subject.py`
- Fallback analyzer: rembg `isnet-anime`
- Mask threshold: 0.5
- Maximum alpha foreground ratio: 0.97
- Tiny-component minimum area ratio: 0.0002
- No generated pixels, inpainting, img2img, or visible-content generation is used.
- Cleanup only removes tiny disconnected evidence components; it does not synthesize missing subject areas.

## Diagnostic-2 results

### Hyakuto Kyoko

- Source SHA-256: `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2`
- Alpha informative: false
- Evidence source: rembg / isnet-anime
- Foreground ratio: 0.4710207612456747
- Subject bbox: x=0, y=0, w=323, h=340
- Visual QA: PASS
- Hair tips, ponytail, torso, arms and major silhouette are retained; orange geometric background is excluded.
### Juufuutei Raden

- Source SHA-256: `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00`
- Alpha informative: false
- Evidence source: rembg / isnet-anime
- Foreground ratio: 0.6008131487889273
- Subject bbox: x=0, y=18, w=340, h=322
- Visual QA: PASS
- Long hair, raised sleeve/hand, rod and torso silhouette are retained; teal geometric background is excluded.

## Mandatory stage artifacts

Canonical runtime artifacts are emitted under:
`artifacts/zerobase2/<case_id>/phase_03/`

Each case contains:
- `03_subject_mask.png`
- `03_subject_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

Persistent diagnostic snapshots are tracked under:
`docs/zerobase/diagnostics/phase03/<case_id>/`
## Determinism

The Phase 3 runner was executed twice with the same source/config.
The mandatory mask and overlay SHA-256 values were identical across both executions.

Kyoko:
- mask: `cfb27caa99ea651cfff8d0bfb161c808ab40485bc6d64c409952e9520ef03cc6`
- overlay: `54597466554ff894f7e3c7942940220bf1d1c661e358d9c847d7bc53f6b2615e`

Raden:
- mask: `33f0b665a89ad9cf279813dad43eb77008d63d1e1a93cc5d1fe06072433dbc0a`
- overlay: `84077f5ddce8fef683c383f8999448873dd0e3977e0b791df6b8d2619dfa975a`

## Regression

- New Phase 3 tests: 4 passed.
- Full ZeroBase suite: 71 passed.
- `git diff --check`: PASS.

## Gate decision

Phase 3 is CLOSED / PASS for Diagnostic-2.
The subject boundary is visually usable for downstream semantic decomposition.

The next phase is **Phase 4: Semantic Part Decomposition**.
No Phase 4+ code may reinterpret a broken subject mask to conceal a Phase 3 failure.
