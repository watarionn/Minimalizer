# SA10.31 real GC001 source-repair detail audit — 2026-10-08

Status: **HOLD / ROLLBACK; no production promotion**.

The SA10.31 diagnostic extends the SA10.30 real GC001 benchmark with a
post-repair AnimeSeg detail overlay and polygon audit. Detail evidence is
strictly clipped by source alpha, colored from the source RGB median, and
reported with its existing material owner. It is observer-only and cannot
change Phase 12 semantic ownership or paste source pixels into the output.

Inputs:

- source: `C:\Work\Temp\macro-gc001\GC001_source.png`
- Phase 4: `C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_04`
- Phase 11: `C:\Work\Temp\sa1023-gc001-clean3\GC001_source\phase_11`
- AnimeSeg mask: `C:\Work\Temp\sa1026-animeseg-gc001-v457\animeseg_mask.png`

Output: `C:\Work\Temp\sa1031-gc001`.

The run produced 14 post-repair detail polygons within the diagnostic budget
of 32. The hard structural gate still failed on `source_topology_changed`, so
the candidate was rolled back. The final candidate PNG remained byte-identical
to baseline; production promotion is false. The overlay and SVG are evidence
artifacts only.
