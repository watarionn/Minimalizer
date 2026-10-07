# SA10.30 real GC001 benchmark — 2026-10-08

Status: **HOLD / NO OUTPUT DELTA; no production promotion**.

The benchmark uses the SHA-bound Phase 11 composition from
`C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_11`, not a stage SVG or a
synthetic payload. Baseline and the SA10.29 AnimeSeg opt-in are run through
`simplify_composed_scene` with the same GC001 source, Phase 4 masks, and Phase
11 composition. AnimeSeg is observer-only and source-alpha clipped.

Runner: `tools/run_sa1030_real_gc001_benchmark.py`.

Artifacts are written outside the repository to `C:\Work\Temp\sa1030-gc001`:
baseline/candidate PNG and SVG plus `metrics.json`. The candidate produced no
PNG delta: Phase 12 structural source repair retained the same 11 primitives,
and no AnimeSeg detail primitive survived selection. Therefore the opt-in is
not promoted. The metrics preserve source silhouette, topology/anatomy,
material/ownership evidence, face-detail count, primitive count, hashes, and
the explicit promotion decision.
