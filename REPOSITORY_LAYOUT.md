# Repository layout

- `CURRENT.md`: canonical current-version pointer. Read first when restoring the project.
- `HANDOFF.md`: current implementation state, invariants, validation, and next actions.
- `RESTORE.md`: restoration rules and source-of-truth guidance.
- `VERSION`: machine-readable stable version.
- `minimalize_engine/`: core processing engine.
- `app/`: CLI/application entry points.
- `gui/`: PySide GUI surface.
- `tests/`: regression and behavior tests. The restored stable snapshot contains 39 `test_*.py` files.
- `tests/assets/corpus/`: original 16-image regression corpus. The legacy `corpus/manifest.json` is retained as historical metadata.
- `tests/assets/corpus_manifest.json`: canonical 16-entry corpus metadata used by the stable tests.
- `tools/`: corpus and character-quality evaluation utilities.
- `examples/input.webp`: retained general source example; byte-identical to `tests/assets/corpus/Night-River-City_general.webp`.
- `.github/workflows/ci.yml`: lightweight permanent GitHub Actions regression guard.
- `RELEASE_NOTES_v0.3.0.md`: stable release notes.
- `BUILD_INFO_v0.3.0.json`: stable build metadata.
- `TEST_RESULTS_v0.3.0.json`: stable test metadata.
- `FINAL_CORPUS_METRICS.json`: stable corpus metrics.
- `docs/history/`: alpha/rc release metadata kept for archaeology only.

Generated debug images, visual-review output, caches, restoration bootstrap payloads, and disposable restoration workflows are intentionally excluded from the GitHub-oriented source snapshot.
