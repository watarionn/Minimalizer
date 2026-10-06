# SA7.37 Required Semantic Mass Reservation — 2026-10-06

Status: SEMANTIC SURVIVAL REPAIR PASS / VISUAL ADOPTION HOLD

SA7.37 introduces a source-only semantic mass reservation layer for critical body roles before later geometric compression.

## Production contract

Inputs:
- original source RGB
- authorized semantic masks

Default roles:
- torso: up to 4 Lab palette clusters
- left_arm: up to 2
- right_arm: up to 2

Explicitly forbidden:
- face reservation
- head reservation
- Golden-derived geometry
- adopted-baseline-derived geometry
- GC001-specific colors or coordinates
- missing-signature RGB/coordinates as production inputs

For each role:
1. cluster role pixels deterministically in Lab space;
2. take the largest connected component per cluster;
3. reject tiny components;
4. reject weak role-local contrast;
5. fit the coarsest polygon satisfying:
   - source coverage >= 0.65
   - expansion ratio <= 1.12
   - semantic-role spill = 0

## GC001 source-only result

Six reservations were produced.

Important GC001 reservations recovered by the generic rule include:
- a large dark torso mass;
- a yellow/green torso mass;
- a large dark right-arm mass.

These align with the semantic ownership identified in SA7.36 without using the SA7.36 missing-signature RGB or coordinates as production input.

## Research overlay evaluation

For evaluation only, the six reservations were painted over the SA7.34 candidate while preserving face/head/hair/major_clothing/accessory masks.

Fresh canonical SA7.35 hard gate:

- required signatures: 16
- Feature Survival before SA7.37: missing=3
- Feature Survival after SA7.37 overlay: missing=0 — PASS
- Forbidden Face Detail: 14.4622% — unchanged FAIL
- overall hard gate: FAIL because face gate still fails

This isolates the effect cleanly: SA7.37 repairs the survival regression without creating or fixing the pre-existing face regression.

## Visual evidence

- Visual Delta vs adopted baseline: 69.8901%
- change vs SA7.34 candidate: 4.3382%
- SA7.34 -> Golden LAB MAE: 33.1502
- SA7.37 research overlay -> Golden LAB MAE: 32.6883
- Browser fallback v12 -> Golden LAB MAE: 16.2422

The reservation stage slightly improves Golden distance while fully recovering source-supported Feature Survival, but still does not beat the v12 floor.

## Decision

Merge the generic source-only semantic mass reservation extractor and CLI.

Do not connect the research overlay directly to production rendering yet.
Do not update the adopted visual baseline.
Do not append SA7.37 to accepted Minimalizer Version History.

## Next

SA7.38 Face Neutralization Path Reconciliation.

The canonical hard gate now shows that the remaining blocker is the face channel:
- Feature Survival: PASS, missing=0
- Forbidden Face Detail: FAIL, 14.4622%

Determine why the SA7.29 candidate family reintroduced internal face variation despite the semantic face-neutralization gate previously reporting PASS, then restore a fresh image-level 0.00% result without reviving eye-like structure.
