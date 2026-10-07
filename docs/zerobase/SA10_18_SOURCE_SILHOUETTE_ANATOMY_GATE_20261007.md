# SA10.18 Source Silhouette / Anatomy Hard Gate — 2026-10-07

Status: IMPLEMENTED / READY FOR REVIEW

SA10.18 binds Phase 14 to source-derived evidence for visible arms, face/head geometry, and the material outer silhouette. These checks are independent hard evidence; aggregate silhouette, primitive economy, saliency, or perceptual scores cannot rescue a failure.

Implementation:

- `evaluate_structural_hard_evidence` records source-visible arm recall, face/head bounding-box and area drift, and outer-boundary recall.
- Phase 14 emits the evidence as an individual `source_anatomy` machine check and preserves topology details.
- Existing source authority, provenance, topology, Feature Survival, and fragmentation policy remain unchanged. The fragmentation threshold is still `0.20`.
- No GC001-specific coordinates, colors, masks, or case branches were added. No image generation or repair was introduced.

Verification:

- Synthetic SA10.18 regressions: omitted source-visible arm and expanded/rounded face with silhouette loss both hard-fail.
- Existing SA10 regression set: `109 passed`.
- `git diff --check`: PASS.
- `GC001 IMG_1205`: source image is not present in this checkout, so no real-source result is claimed.

Next handoff:

Run the canonical GC001 source job when `IMG_1205` is available, then perform independent visual QA and preserve the artifacts. After that, introduce in order: source-derived vectorization, shape matching, topology preservation, saliency/perceptual observer metrics, and constrained `diffvg` research integration. These remain subordinate to the hard gates.
