# SA10.28 AnimeSeg source constraints - 2026-10-08

Status: IMPLEMENTED / READY FOR REVIEW. This is a Phase 12 observer constraint,
not a Phase 12 closure and not production authority.

The new adapter reads the 12-class AnimeSeg RGB mask and clips every class mask
to the source PNG alpha (`alpha >= 1`). Unknown RGB values are counted and
excluded. It records source/mask SHA-256 when using the file adapter. The
result contains only source-derived saliency evidence; it cannot create pixels,
reassign semantic ownership, or authorize rendering.

GC001 diagnostic inputs:

- source: `C:\Work\Temp\macro-gc001\GC001_source.png`
- observer mask: `C:\Work\Temp\sa1026-animeseg-gc001-v457\animeseg_mask.png`
- output root: `C:\Work\Temp\sa1028-gc001`

The fresh output is a diagnostic artifact only. The existing isolated AnimeSeg
venv and the SA10.27 observer remain unchanged. No holdout is opened and no
Phase 12/production authority is changed.

Validation required for review: focused SA10.28 and observer tests, compileall,
`git diff --check`, and deterministic replay of the GC001 constraint artifact.
Next canonical step remains Phase 12 review.
