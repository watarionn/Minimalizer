# G11 First Blind Run

G11 was sealed before execution and run once against the frozen observer and production baseline.

## Result

- 5/5 cases produced non-zero hair, face-skin, limb, and accessory evidence.
- 5/5 bindings had zero unresolved features.
- 5/5 production bridges were READY.
- Each output used 12 authorized primitives.
- Contour envelopes and local accent rendering were active for all cases.
- Golden raster and manual semantic labels were not used.
- Observer mean elapsed time: 0.5495582200121134 s/image.
- Peak CUDA memory: 1378.61328125 MiB.

Artifact: GBLIND_G11_FRESH_20261005_first_run.zip
SHA-256: b7bcb01d61a2af624b641e4d58c9e372e09aa64480cce5ae3470f03c84ddbc7d

## Review

The contour/accent mechanism generalized structurally to the fresh suite. The next generic bottleneck is palette locality: authorized palette extraction currently samples the whole authorized bbox, so pixels outside the actual semantic topology can contaminate dominant/accent colors. The next implementation should restrict palette evidence using already-authorized mask topology without adding semantics or case-specific rules.
