# SA7.33 Background Field Geometry Re-authoring — 2026-10-06

Status: GEOMETRY CONTRACT PASS / VISUAL ADOPTION HOLD

SA7.33 converts the SA7.32 source-only background evidence into a bounded set of large background field polygons.

## Production contract

- source RGB + source-derived subject mask only
- at most 3 background fields
- border-connected background authority
- deterministic source-color clustering
- connected-component cleanup
- adaptive contour simplification
- minimum source coverage: 0.60
- maximum expansion ratio: 1.12
- subject overlap: exactly 0
- unsupported cases fail closed
- Golden and Browser fallback v12 are never inference inputs

A uniform background field that completely wraps a subject is intentionally rejected by the current polygon-only representation because a single filled polygon would erase the subject hole. Open concavities are handled by selecting the coarsest contour approximation that passes the subject-overlap and support guards.

## GC001 geometry

Two safe fields were produced:

1. RGB [255,134,46]
   - source area: 23,451 px
   - rendered area: 23,609 px
   - source coverage: 0.9874
   - expansion ratio: 1.0067
   - subject overlap: 0
   - polygon vertices: 37

2. RGB [254,35,8]
   - source area: 16,778 px
   - rendered area: 17,119 px
   - source coverage: 0.9938
   - expansion ratio: 1.0203
   - subject overlap: 0
   - polygon vertices: 29

## GC001 visual evaluation

The SA7.33 background fields were inserted behind the unchanged SA7.29 semantic subject SVG.

Hard gates:
- Visual Delta vs adopted baseline: 64.68% — PASS
- Feature Survival: 16/16, missing=0 — PASS
- Forbidden Facial Detail: 0.00% — PASS
- Topology: PASS
- Anatomy: PASS
- Face Neutralization: PASS

Golden-distance evidence:
- SA7.29 candidate -> Golden LAB MAE: 54.94
- SA7.33 candidate -> Golden LAB MAE: 32.67
- Browser fallback v12 -> Golden LAB MAE: 16.24

Role-local background contribution:
- SA7.31 / SA7.30 candidate background weighted gap: 0.16390
- SA7.33 background weighted gap: 0.09078
- reduction: about 44.6%

This strongly supports the SA7.31 attribution that background/composition was the dominant remaining error source. However SA7.33 still does not beat the Browser fallback v12 regression floor, so it is not an adopted visual version.

## Decision

Merge the generic SA7.33 source-supported geometry contract.
Do not update the adopted visual baseline.
Do not append SA7.33 to accepted Minimalizer Version History.

Next: SA7.34 Background Multi-field Scene Integration / Hole-safe Composition. Preserve field relationships while integrating background geometry into the canonical scene, including an explicit strategy for wrapped-background cases that cannot be represented by one filled polygon.
