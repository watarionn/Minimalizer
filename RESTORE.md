# Restore Minimalizer

Canonical current state: **v0.3.0 stable**.

Restore order:
1. Read `CURRENT.md`.
2. Read `VERSION`.
3. Read `RELEASE_NOTES_v0.3.0.md` and release metadata.
4. Treat all alpha and rc builds, including `v0.3.0-alpha8 Character-specific Quality / Retry`, as historical checkpoints only.

Do not resume from alpha8. Resume from v0.3.0 stable. The next development line should be v0.3.x or v0.4.0 while preserving the v0.3.0 regression baseline.
