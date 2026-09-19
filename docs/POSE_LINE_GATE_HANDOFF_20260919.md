# Pose-line gate exact-binding handoff (2026-09-19)

## Resume point
Worktree: `C:\Users\watar\Documents\GitHub\Minimalizer-pose-line-contract`
Branch: `feature/pose-line-guidance-contract`
Do not merge/deploy/main without explicit user authorization.
Do not touch the separate Approved-78 hierarchy-cut calibration worktree.

## Current implementation
`apply_pose_aware_line_gate()` exists in `minimalize_engine/v2/analysis_guidance.py`.
Gate formula: `weight = floor + (1-floor) * pose_support`.
Current tested default candidate before sensitivity work was floor=0.15.
Pose relation weight used in audit: 0.06. Line prior strength: 0.35.

## Exact-binding 18 audit
baseline / pose+old-gate / pose+gate-v2 completed for all 18.
gate-v2 at floor=0.15: invariant failures 0/18.
Cross-tag merges: baseline 426 -> gate-v2 413.
Mean guide-retention delta: +0.00105997.
Main regressions: Kobo-Kanaeru retention -0.0054; Raora-Panthera retention -0.0130.
Raora additionally had visual groups -4, selected regions +2, contour IoU -0.0089, complexity -43.36.## Two-case sensitivity sweep
Temp workspace: `%TEMP%\minimalizer_pose_line_gated_eval_20260919`
Script: `run_gate_v2_sensitivity2.py`
Result: `v2_sensitivity2_eval.json`
Grid: floor 0.10/0.15/0.20 x line strength 0.25/0.35.

Kobo was unchanged across all six candidates:
retention -0.0054, groups 0, regions 0, contour IoU 0, complexity -7.74, cross-tag merges -2.

Raora was unchanged/regressed for five candidates.
The only strong recovery was floor=0.20 + line strength=0.35:
retention -0.0003, groups 0, regions 0, contour IoU 0, complexity -1.62, cross-tag delta 0, invariant failures 0.
This is the current gate-v2 candidate.

## Integration closure (2026-09-20)
Gate-v2 is now fixed branch-locally at floor=0.20, pose weight=0.06, line strength=0.35.
Exact-binding 18: invariant failures 0/18; cross-tag merges 426 -> 413 (-13); mean guide-retention delta +0.00253296.
Approved-78: invariant failures 0/78; cross-tag merges 1685 -> 1653 (-32); mean contour IoU delta +0.000220; mean guide-retention delta -0.000358.
Focused watch cases: Mori-Calliope #10 (contour -0.003932), Gawr-Gura #74 (contour -0.001566), Hanazono-Sayaka #67 (retention -0.044897 without structural-count/contour regression), Ceres-Fauna #75 (retention -0.014736 with contour +0.006611).
The default floor is protected by a regression test that calls `apply_pose_aware_line_gate()` without an explicit floor.

Integration tests covering pose-line + RTMLib + DeepLSD + Region Merge: 51/51 passed.
Full `tests` suite: 563 passed, 2 failed, 1 warning.
Both failures are pre-existing fixture availability failures: `tests/assets/false_face_phase85.png` is absent and raises FileNotFoundError in two face-quality tests.
A filesystem search plus `git ls-files` / `git log --all -- tests/assets/false_face_phase85.png` found no copy or tracked history for that fixture in the inspected repository/worktrees.
No failure was attributed to the pose-line/Region Merge changes.
`git diff --check` passes apart from the known LF/CRLF working-copy warning.

## Resume / next action
The pose-line gate v2 calibration and integration audit are closed as a branch-local fixed candidate.
Keep Mori-like contour cases on the watch list during later integration validation.
Do not modify the separate Approved-78 hierarchy-cut calibration worktree.
Do not merge, deploy, or modify main without explicit user authorization.
If integration work continues before merge authorization, the next useful step is a final branch diff/review and commit-boundary preparation, without committing unrelated pre-existing work.