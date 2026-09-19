# Pose-line gate v2 fixed-candidate audit (2026-09-19)

## Decision
Fix the branch-local gate-v2 candidate at `floor=0.20`.
Audit conditions: pose relation weight `0.06`, line prior strength `0.35`.
This is not authorization to merge, deploy, or modify main.

## Exact-binding 18 result
- invariant failures: 0/18
- cross-tag merges: baseline 426 -> gate-v2 413 (-13)
- mean guide-retention delta: +0.00253296
- retention: 8 better / 2 worse / 8 unchanged
- selected-region mean delta: 0.0; max increase: 0
- visual-group mean delta: +0.38889; max absolute delta: 2
- mean complexity delta: -4.46444
- mean vertex delta: -11.33333

Compared with floor=0.15, the material changes were Mori-Calliope and Raora-Panthera.
Raora recovered from retention -0.0130 to -0.000260, and groups/regions/contour returned to baseline.
Mori retention improved by +0.013783 vs floor=0.15, while contour IoU moved -0.003932 vs baseline.

## Focused three-case audit
Mori: retention +0.013783, cross-tag -1, long-line +0.013407, contour IoU -0.003932, complexity -2.52.
Kobo: retention -0.005431, cross-tag -2, long-line +0.036299, groups/regions/contour unchanged, complexity -7.74.
Raora: retention -0.000260, cross-tag 0, groups/regions/contour unchanged, complexity -1.62.

Kobo's retention metric remains lower, but structural counts and contour are unchanged while long-line support improves.
Treat this as a residual metric tradeoff, not a blocker for the fixed candidate.
Mori's contour delta is retained as a watch item for broader Approved-set validation.

## Validation
The default of `apply_pose_aware_line_gate()` is now `floor=0.20`.
Relevant pose/line/region-merge tests: 33 passed.
`git diff --check`: passed (Git emitted only the existing LF/CRLF working-copy warning).

## Approved-78 full validation
The fixed candidate was evaluated on all 78 Approved cases with baseline, old gate, and gate-v2 variants.

- invariant failures: 0/78
- cross-tag merges: baseline 1685 -> gate-v2 1653 (-32); old gate reduced by 28
- mean contour IoU delta: +0.000220
- mean guide-retention delta: -0.000358 (old gate: -0.001321)
- mean complexity delta: -0.565
- mean vertex delta: -0.949

Focused review of the largest tradeoffs did not identify a reason to change the fixed floor:
- Hanazono-Sayaka (#67): retention -0.044897, but contour IoU / selected regions / visual groups unchanged; cross-tag -1. Gate-v2 also recovers most of the old-gate structural reduction.
- Ceres-Fauna (#75): retention -0.014736, contour IoU +0.006611, cross-tag -2.
- Gawr-Gura (#74): retention -0.002816, contour IoU -0.001566; selected regions / visual groups / complexity unchanged.
- Mori-Calliope (#10): retention +0.013783, contour IoU -0.003932, cross-tag -1, complexity -2.52. This remains the primary contour watch case.

Conclusion: retain `floor=0.20` as the branch-local fixed candidate. The observed regressions are localized metric tradeoffs rather than an Approved-78-wide structural failure.

## Next
Lock the default floor with a regression test and keep monitoring Mori-like contour cases in later integration validation.
Keep all work on `feature/pose-line-guidance-contract`.
No merge/deploy/main without explicit user authorization.
