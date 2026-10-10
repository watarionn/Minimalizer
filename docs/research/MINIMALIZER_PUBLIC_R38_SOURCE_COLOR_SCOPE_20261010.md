# R38 source color evaluation scope (2026-10-10)

Input: frozen source-free R25 RGB-error report, R30 signed-mask and R36 full-owner Chrome diagnostics. No original photos or palette changes in this stage.

R38 review gate is HOLD until source-only independent semantic annotations exist for arm, clothing, tie and held object. R37 Chrome pixel-exact owner masks do not prove image/part semantic correctness.

Do not promote a source-color-only optimization based on per-owner MAE, because owner masks overlap and foreground colors may have intentionally been reduced. The face-hidden policy remains unchanged. Original Stage8 budgets and R6 eight blockers remain unsatisfied.

Research branch only; no main merge, no production deploy.