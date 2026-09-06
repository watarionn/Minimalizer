# Repository layout

- `CURRENT.md`: canonical current-version pointer. Read first when restoring the project.
- `HANDOFF.md`: current implementation state, invariants, validation, and next actions.
- `VERSION`: machine-readable stable version.
- `minimalize_engine/`: core processing engine.
- `app/`: CLI/application entry points.
- `gui/`: PySide GUI surface.
- `tests/`: regression and behavior tests.
- `tests/assets/corpus/`: 16-image regression corpus and manifest.
- `tools/`: corpus and character-quality evaluation utilities.
- `examples/input.webp`: retained general source example used by the project.
- `RELEASE_NOTES_v0.3.0.md`: stable release notes.
- `BUILD_INFO_v0.3.0.json`: stable build metadata.
- `TEST_RESULTS_v0.3.0.json`: stable test metadata.
- `FINAL_CORPUS_METRICS.json`: stable corpus metrics.
- `docs/history/`: alpha/rc release metadata kept for archaeology only.

Generated debug images, visual-review output, caches, and other disposable artifacts are intentionally excluded from the GitHub-oriented source snapshot.
