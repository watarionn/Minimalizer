# Stage8 signed ring exact-coordinate probe (2026-10-09)

Source: private SHA-signed SA10.34 Stage8 `phase8_adaptive_source_contour_research.json`, 11 source owners each case. This is **a research diagnostic only**, no original files changed.

## Observed source-ring structure

| Character | Rings vertex count | Components vertex count | Adjacent duplicate points | Collinear point occurrences |
|---|---:|---:|---:|---:|
| GC001 | 3,604 | 3,342 | 0 | 45 |
| Raden | 2,370 | 2,259 | 0 | 15 |

The first execution incorrectly used `components` rather than `rings[].points`. It correctly failed closed on a 3,342-versus-3,604 discrepancy. The corrected source parser independently reconstructed exactly the archived Stage8 `adaptive_total` counts.

**Zero adjacent exact duplicates** means simply deduplicating successive ring vertices will not yield meaningful reduction. Collinear occurrences are only **unverified** candidates: some are in source rings with fewer than three vertices or at polygon seams. Even if all 45/15 candidate occurrences could safely disappear, they would not solve historic overages GC001 +1,717 and Raden +958. Do not assume this upper bound is realizable.

The raw source geometries may include diagonal contact, distinct islands and holes. Any actual edit requires per-owner signed raster replay with topology, original SHA and DPR4 browser validation. The current probe does not perform that mutation or authorizes zero vertex removals. No generated fill, face details, production integration, merge or deployment.

Research files: `tools/research/public_geometry_js/stage8_lossless_ring_probe.py`, `test_stage8_lossless_ring_probe.py`. Two unit checks PASS on a connected Windows PC: signed owner consistency/release HOLD and owner drop fail-closed.

**Decision:** exact-duplicate elimination avenue closed. Subpixel and topology-safe contour representation still needed; next investigate geometric sharing or versioned cap policy migration without secretly changing the current policy.
