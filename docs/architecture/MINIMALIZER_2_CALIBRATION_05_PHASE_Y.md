# Minimalizer 2.0 Calibration 05 Phase Y

Status: post-cutover acceptance passed locally on RDC.
Date: 2026-09-17

## Purpose

Phase Y validates the approved Phase X Default Migration through a real local HTTP server and packages release/rollback evidence without publishing remotely.
The acceptance run starts the FastAPI application with Uvicorn and exercises `/api/minimalize` through HTTP multipart requests rather than relying only on TestClient dispatch.

## Live HTTP acceptance

Eligible browser Standard request:
- opaque PNG
- Standard mode
- level 4
- PNG output
- white background
- browser marker `X-Minimalizer-Browser-Default: v2`

Observed response:
- HTTP 200
- `X-Minimalizer-Route: v2`
- `X-Minimalizer-Mode: standard`
- `X-Minimalizer-Configured-Analysis-Max-Side: 400`
- `X-Minimalizer-V2-Preset: minimal`
- `Content-Type: image/png`

Compatibility cases were also exercised through the live server:
- Standard SVG + white background -> `legacy`
- transparent Standard PNG + white background -> `legacy`
- direct `/api/minimalize` caller without browser marker -> `legacy`
- Rinka Reference -> `legacy`

All compatibility cases returned HTTP 200 with their expected media type.
The root HTML exposed white as the selected Standard background.
The served JavaScript contained the browser marker header and Standard PNG preview selection.

## Rollback verification

An endpoint-level regression test temporarily substitutes the migration contract state with `legacy_default` while leaving canonical code at `v2_standard_default`.
The same otherwise V2-eligible browser request then returns `X-Minimalizer-Route: legacy`.
This confirms rollback remains a routing-state operation and needs no data migration.

Default-migration endpoint suite after adding the rollback proof: `10 passed, 1 warning`.
The warning is the existing Starlette/TestClient deprecation warning only.

## Release preparation

Release candidate behavior is now documented as:
1. browser Standard default uses V2 only inside the approved compatibility envelope
2. direct legacy API callers retain legacy behavior unless they send the browser marker
3. SVG, transparency-sensitive requests, custom detail controls, Rinka Reference, and Color Strip stay legacy
4. hosted V2 default uses `analysis_max_side <= 400`
5. V2 execution errors are surfaced and never silently retried through legacy
6. rollback is `current_state = legacy_default`

No push, PR, merge, deployment, or GitHub Actions execution occurred in Phase Y.

## CI readiness remediation

The GitHub workflow was inspected locally without running GitHub Actions.
Its trigger contract is `pull_request` plus pushes to `main`; feature-branch pushes alone do not trigger the workflow.
The workflow still contained stale Web/Rinka expectations from older releases, so Phase Y updates CI locally before any PR:
- Web version expectation `0.8.0 -> 0.13.0`
- Rinka version expectation `phase10 -> phase16`
- Color Strip selection modes now include `characteristic`
- Web test step now includes `tests/test_v2_default_migration.py`
- real-server smoke now verifies `/api/v2/info` and an actual V2-default browser request
- Rinka evaluation paths/artifact labels now use Phase 16
- obsolete aggregate mean shape/vertex reduction thresholds were removed rather than replaced with post-hoc thresholds
- the still-valid segmentation, plane, coverage, identity, silhouette, cap, and macro-shadow safety guards remain enforced

Local CI-definition verification:
- YAML parse: PASS
- current Phase 16 evaluation completed successfully on 16 cases
- retained Phase 16 safety guard assertions: PASS
- CI Web API/UI test command: `49 passed, 1 warning`
- CI V2-default real-server request using `examples/input.webp`: HTTP 200, route `v2`, cap `400`, preset `minimal`, valid PNG signature
- stale Phase 10 workflow markers searched: none found
