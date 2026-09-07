# Restore Minimalizer

Canonical current state: **v0.3.0 stable**.

The GitHub repository contains the restored v0.3.0 stable implementation, tests, tools, and original 16-image regression corpus. Do not reconstruct the implementation from memory or from an alpha/rc checkpoint.

Restore order:
1. Read `CURRENT.md`.
2. Read `HANDOFF.md`.
3. Read `README.md` and `REPOSITORY_LAYOUT.md`.
4. Inspect the actual source under `minimalize_engine/`, `app/`, and `gui/` before making changes.
5. Inspect `tests/` and `tests/assets/corpus_manifest.json` before changing stable behavior.
6. Read `VERSION` and the stable release metadata as needed.
7. Treat all alpha and rc builds, including `v0.3.0-alpha8 Character-specific Quality / Retry`, as historical checkpoints only.

Do not resume from alpha8. Resume from v0.3.0 stable. The next development line should be v0.3.x or v0.4.0 while preserving the v0.3.0 regression baseline.
