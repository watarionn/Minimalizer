# SA10.32 SVG contour candidate research (2026-10-08)

Status: EXPERIMENTAL / NOT INTEGRATED / PRODUCTION HOLD

Grounding: PR #222 SA10.31 handoff and real GC001 topology rollback. The current
prototype extracts deterministic polygon proposals from **source part masks** for
**existing** face/hair owners only. It does not add a VectorScene primitive,
draw a facial feature, paste pixels, or invoke generative image processing.

## Research contract

- Source raster remains the authoritative ground truth; SVG is only an
  optional representation of observed boundaries.
- Reject missing masks, mismatched dimensions, holes, multi-island regions,
  invalid topology, or insufficient polygon-to-source IoU.
- Existing part ownership and material cannot be reassigned.
- Before any scene update, the existing SA10.18/20/22/31 hard gates must
  independently verify source boundary, topology, connectivity, anatomy,
  fragmentation, protected regions, and primitive budget.
- Any regression or absent backend results in rollback. No face feature
  overlay or standalone eye/mouth geometry is permitted.
- Never use blind holdouts to tune thresholds.

## Next verification

1. Run focused test_sa1032_source_svg_contour_proposals.py and full
   tests/zerobase, compileall, and diff-check.
2. Wire diagnostic proposals into an opt-in, non-rendering report.
3. Compare real GC001 source, baseline and proposal evidence; do not claim
   improvement until candidate SVG/PNG actually differs and all gates pass.
4. Keep production unchanged until independent visual review and deployment
   verification.

This commit is a research scaffold, not SA10.31 completion or production
promotion.
