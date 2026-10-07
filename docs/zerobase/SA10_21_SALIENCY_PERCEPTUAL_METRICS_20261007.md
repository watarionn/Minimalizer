# SA10.21 Saliency / perceptual metrics integration — 2026-10-07

Status: IMPLEMENTED / READY FOR REVIEW

SA10.21 adds deterministic, source-derived region perceptual evidence to the
Phase 14 evaluator. Face/head, left/right arm, and the material outer boundary
are weighted from Phase 4 semantic masks. The report emits per-region MAE,
SSIM, pixel weight, provenance, backend availability, and an aggregate only as
observer evidence. The aggregate is never a gate or authority.

The existing authority hierarchy is unchanged: SA10.18 source/anatomy and
silhouette, SA10.20 topology, and the Phase 5 structural graph remain hard
gates; SA10.19 shape/vector evidence and SA10.21 perceptual evidence cannot
rescue a structural failure. No case-specific branch, threshold weakening,
generative repair, or visible-content generation was added.

Dependency decision:

- SSIM-like deterministic evidence uses existing NumPy/OpenCV dependencies.
- Existing DINOv3 observer foundation is reusable through injection, but no
  model or runtime is imported or downloaded by this evaluator.
- LPIPS is an optional injected backend only; no heavy dependency is added to
  the required environment. Missing DINOv3/LPIPS is explicit unavailable
  evidence and does not create authority.

Verification:

- Synthetic regression proves equal-area salient face distortion produces
  stronger evidence than non-salient distortion.
- Synthetic regression proves missing heavy backends remain non-authoritative.
- Focused SA10.18/SA10.19/expanded regression: 16 passed.
- `python -m compileall -q minimalizer_zerobase`: PASS.
- `git diff --check`: PASS.

Next handoff: constrained diffvg optimization under all existing hard gates,
with rollback preserved. This change remains source/tests/docs/dependency
record only; no artifact mirror, Drive save, push, merge, or deploy performed.
