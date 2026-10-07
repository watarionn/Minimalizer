# HND-20261007 SA10.18 — Source Silhouette / Anatomy Gate

Status: IMPLEMENTED / READY FOR REVIEW

## Scope

SA10.18 adds an evaluation-only, fail-closed gate for source evidence and candidate silhouette. It does not vectorize, author geometry, or promote shape matching, topology, saliency, or perceptual metrics to rendering authority. `diffvg` remains an optional research backend behind the existing boundary.

## Hard contract

- Source and candidate masks must have identical dimensions.
- Silhouette IoU must be at least 0.96.
- SA10 fragmentation penalty must be `<= 0.20`; `0.20` passes and values above it hard-fail.
- Connected-component and hole topology must be unchanged.
- Missing required anatomy evidence hard-fails.
- Shape matching, saliency, and perceptual scores are evidence only and cannot clear a hard failure.
- `can_override_hard_fail` is always `false`.

## Source evidence

The report records source mask pixel count and source topology, candidate equivalents, threshold policy, and every hard-failure reason. The implementation is generic and contains no GC001-specific coordinates, colors, or feature constants.

## Regression / cases

- Synthetic regression: identical mask PASS; exact fragmentation boundary PASS; `0.200001` FAIL; topology mutation FAIL even with perfect observer scores; missing required anatomy FAIL.
- GC001 / `IMG_1205`: must be run as a separate real-source evidence job using the canonical source mask and saved report. No Golden pixels may be used as inference input.
- Diagnostic-2 and Approved corpus promotion remain blocked until real source evidence and visual review exist.

## Definition of Done

- [x] Source implementation and schema added.
- [x] Synthetic regression added.
- [x] Vectorization / shape matching / topology / saliency / perceptual authority boundaries explicit.
- [ ] GC001 `IMG_1205` real-source artifact attached and independently reviewed (not present in this checkout; no claim made).
- [x] Existing SA10 regression suite completed: 109 passed.
- [x] Synthetic source-arm / face-head / outer-silhouette regressions completed.
- [x] `pytest` focused and relevant suite passes.
- [x] `git diff --check` passes.
- [ ] Commit created after review.

## Completion and next handoff

SA10.18 implementation is complete for this checkout. The Phase 14 evaluation now consumes source-bound structural evidence and exposes anatomy and outer-silhouette failures independently of aggregate metrics. The next review gate is a real-source GC001 `IMG_1205` run, when the canonical source artifact is available, followed by visual QA and artifact preservation.

The next implementation sequence is explicitly: (1) source-derived vectorization, (2) shape matching, (3) topology preservation, (4) saliency/perceptual metrics as non-authoritative observers, and (5) constrained `diffvg` research integration behind the existing opt-in boundary. None may override the hard source/anatomy/topology gates or write generated visible content.

## Verification commands

```powershell
pytest -q tests/zerobase/test_sa1018_source_silhouette_anatomy_gate.py
git diff --check
```

No push, merge, deploy, or Drive write is authorized by this handoff.
