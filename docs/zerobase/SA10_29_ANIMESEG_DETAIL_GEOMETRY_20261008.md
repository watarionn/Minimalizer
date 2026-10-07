# SA10.29 AnimeSeg source-bound detail geometry - 2026-10-08

Status: IMPLEMENTED / READY FOR REVIEW. The path is opt-in and does not alter
the default Phase 12 production route.

When enabled, cached AnimeSeg class masks for hair, face, eyes, eyebrows, nose,
and mouth are clipped to immutable source alpha. External contours become
deterministic polygon candidates and RGB colors are sampled from the source
pixels covered by each observed mask. Unknown classes, empty masks, invalid
shapes, and failed existing Phase 12 hard gates fail closed. No source image
paste or generative pixels are used.

The adapter is non-authoritative (`authority=false`); it cannot reassign
semantic ownership. Detail classes are attached only to the existing hair/face
owners so the existing silhouette and critical-part gates remain decisive.
The option is `StyleSimplificationPolicy(animeseg_source_detail_geometry=True)`
with `animeseg_source_constraints=...` passed to `simplify_composed_scene`.

GC001 comparison was not promoted in this isolated worktree because the
canonical GC001 Phase 11 composition artifact was not present beside the
cached source and AnimeSeg mask. No holdout was opened. The implementation
and synthetic/focused gates remain the evidence for this commit; a canonical
GC001 SVG/PNG comparison must be run before adoption.
