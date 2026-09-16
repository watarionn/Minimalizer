# Minimalizer 2.0 Calibration 05 Phase W

Status: cutover package staged; execution intentionally not performed.

## Purpose

Phase W converts the verified Phase U/V evidence into an explicit, reversible cutover package.
This phase stops immediately before changing the browser default because cutover requires
explicit user approval.

## Candidate cutover

Target browser rollout state: `v2_standard_default`.
Eligible Standard PNG, white-background, opaque-source requests route to V2.
The hosted V2 route must keep the Phase T `analysis_max_side <= 400` envelope.
SVG and transparency-sensitive requests remain legacy-routed.
Rinka Reference and Color Strip remain legacy-routed.
No automatic fallback is introduced after a V2 execution error.

## Rollback

Rollback target is `legacy_default`.
Rollback is routing-only and requires no persistent data migration.
The existing legacy endpoint remains available throughout the cutover.

## Approval boundary

The current browser JavaScript still posts to `/api/minimalize`.
No production default, PR, main, merge, or deployment change is part of this staging step.
After explicit approval, implementation must be followed by focused migration/Web tests,
V2 regression, full-repository regression, and a post-cutover browser-route verification.

## Evidence

Phase U release candidate: PASS.
Phase V final pre-cutover gate: PASS.
Phase W cutover package: READY, NOT EXECUTED.
