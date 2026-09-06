# Minimalizer Handoff

## Restore order

1. Read `CURRENT.md`.
2. Read this file.
3. Read `README.md` and `REPOSITORY_LAYOUT.md`.
4. Treat `v0.3.0 stable` as the regression baseline.
5. Inspect code and tests before changing behavior.

## Current state

Minimalizer v0.3.0 stable is complete. The original product goal remains simple: input image -> minimalized graphic. Core minimalization quality takes priority over optional character-specific features.

Release validation recorded at v0.3.0:
- 39 test files.
- 156 tests passed / 0 failed when completed in batches.
- 16/16 corpus images processed successfully.
- Mean corpus quality about 0.7893.
- Mean identity about 0.9484.
- Mean silhouette about 0.9114.
- 8192x6373 (52.21 MP) stress input completed successfully.
- `compileall` passed.

A single-process full pytest run exceeded the interactive execution window and is not counted as a completed pass.

## Important stable behavior

- Conservative thin/noisy rectangle cleanup.
- Near-background fragment cleanup with semantic safeguards.
- Same-role union only when real contour connectivity is preserved.
- Experimental role-fragment merging remains OFF by default.
- Adaptive polygon simplification uses strict local raster IoU protection.
- Conservative polygon -> rectangle/ellipse promotion.
- Character identity and semantic geometry receive protection.
- Face primitive drawing is OFF by default.
- Advanced GUI controls are hidden by default.
- High-resolution RGB input preparation avoids an unnecessary eager full-size copy.

## Recommended next work

Before starting new quality work, audit the direct default of `cleanup_minimal_shapes(... promote_rectangle_iou)` against the stable config default of 0.985 and add a regression test if needed. Also add a fully opaque RGBA high-resolution smoke test.

Then improve weaker corpus cases without regressing the stable baseline, especially identity/silhouette outliers. Prefer `v0.3.1` for safe fixes and `v0.4.0` for broader algorithm changes.
