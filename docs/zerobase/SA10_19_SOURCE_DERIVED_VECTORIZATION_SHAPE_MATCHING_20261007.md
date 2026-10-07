# SA10.19 Source-derived vectorization / shape matching — 2026-10-07

Status: IMPLEMENTED / READY FOR REVIEW

SA10.19 adds deterministic source-derived contour evidence to the Phase 14
evaluation. OpenCV `findContours`, Hu moments, and `matchShapes(I1)` compare
the source and candidate outer masks. The evidence is serialized in
`details.source_shape_evidence` and is diagnostic only.

Authority order is unchanged: SA10.18 source/anatomy/silhouette and topology
hard gates remain authoritative. Shape matching and vectorization explicitly
cannot turn a hard failure into a pass. No case-specific branch, generated
repair, inpainting, or visible-content generation was added.

VTracer was evaluated as an optional backend. The upstream Python package
declares `MIT OR Apache-2.0`; this is within the repository's permitted
boundary. It is not a required dependency and is not installed automatically.
When present, availability is recorded in `details.vectorization_backend`;
OpenCV contour evidence remains the compatible deterministic baseline.

Verification:

- Synthetic SA10.19 tests: 3 passed.
- Focused SA10.18 plus existing expanded SA10 regression: 12 passed.
- Existing `tests/zerobase` suite: 872 passed.
- `python -m compileall minimalizer_zerobase`: PASS.
- `git diff --check`: PASS.

Next handoff: allow topology preservation improvements to be researched and
tested next. Shape/vector evidence remains subordinate to topology and the
existing source/anatomy hard gates.
