# Minimalizer CURRENT

Current release: **v0.3.0 stable**

This file is the canonical restoration pointer.

## GitHub source of truth

The repository now contains the restored **v0.3.0 stable implementation snapshot** itself, not only handoff metadata.

- Core source: `minimalize_engine/`, `app/`, `gui/`
- Regression tests: `tests/` with 39 `test_*.py` files
- Stable corpus: `tests/assets/corpus/` with 16 original images
- Corpus metadata: `tests/assets/corpus_manifest.json`
- Evaluation tools: `tools/`
- Stable sample input: `examples/input.webp`

The restoration workflow verified that all 16 corpus entries exist, that 39 test files exist, that the restored Night River asset matches its original SHA-256, and that the Python source tree passes `compileall`.

## Version rule

- `v0.3.0-alpha8 Character-specific Quality / Retry` is a historical checkpoint, not the current state.
- All alpha and rc builds are historical development checkpoints.
- Resume future work from **v0.3.0 stable** as the regression baseline.
- The next development line should be `v0.3.x` for conservative fixes or `v0.4.0` for larger quality changes.

Read next: `HANDOFF.md`.
