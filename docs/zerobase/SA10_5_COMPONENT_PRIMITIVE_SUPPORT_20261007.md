# SA10.5 Component-to-Primitive Support — 2026-10-07

Status: MEASUREMENT CONTRACT COMPLETE / GC001 SOURCE MASK RECOVERY REQUIRED

Added `evaluation/component_primitive_support.py`.

Measurement is now direct:
- reconstruct the same major source-component frame used by SA7.43;
- rasterize each emitted macro polygon;
- component represented iff one emitted primitive covers at least 50% of that source component;
- primitive source-supported iff at least 65% of its raster area overlaps the role source mask.

These are measurement-contract thresholds, not quality gates.

Fail-closed checks:
- thresholds outside [0,1]
- missing role masks
- source component frame mismatch against adaptive-budget provenance
- emitted primitive count mismatch against adaptive-budget provenance

No Golden raster, DINO score, teacher label, or allocation count can create support evidence.

Verification:
- SA10.5 through SA10.1 focused chain: 24/24 PASS

GC001 status:
- historical SA7.43 budget and scene reports are preserved;
- the exact role source-mask arrays required for overlap remeasurement were not found in GitHub/Drive artifact search in this stage;
- therefore no GC001 support ratio is claimed yet.

Next: SA10.6 should make role-mask preservation part of the canonical evaluation artifact path, regenerate/recover GC001 masks from the canonical source pipeline, then run SA10.5 and reassemble SA10.3.
