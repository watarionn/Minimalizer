# Minimalizer

Minimalizer converts an input image into a minimal graphic built from a small palette and geometric Shapes.

**Current release: v0.3.0 stable.**

For project restoration or continuation in another ChatGPT conversation, read `CURRENT.md` first, then `HANDOFF.md`.

## Project priority

The core product goal is intentionally simple: **input image -> minimalize**. Improvements to general minimalization quality take priority over optional features.

## Main components

- `minimalize_engine/` core image-analysis and Shape pipeline
- `app/` CLI/application entry points
- `gui/` desktop GUI
- `tests/` regression suite and 16-image corpus
- `tools/` evaluation utilities

## Stable v0.3.0 highlights

- Conservative low-value/noisy geometry cleanup
- Near-background fragment cleanup
- Adaptive polygon simplification with raster-IoU protection
- Safe primitive promotion
- Character/semantic preservation safeguards
- Face primitives OFF by default
- Basic GUI first, advanced controls hidden by default
- 8K-class input durability improvements

See `RELEASE_NOTES_v0.3.0.md` for release detail and `REPOSITORY_LAYOUT.md` for repository organization.


### Optional Jev Semantic Advisor (development QA)

The layered-person development path includes an opt-in semantic QA exporter at
`tools/export_jev_semantic_candidates.py`.

It probes hidden planes deterministically and exports only planes whose
restoration actually changes rendered pixels. An external Jev sidecar may label
those numeric candidates for QA review. The advisor does not modify output,
visibility, masks, merges, pruning, or primitive geometry, and Jev receives no
image bytes.

See `docs/JEV_SEMANTIC_ADVISOR.md`.
