# Geometry Mass production integration — 2026-09-26

## Scope

This handoff closes the post-Shading-Flatten Approved-68 audit for Semantic Geometry Mass and records the production integration policy.

Approved-68 is the Approved-78 corpus with orders 59–68 excluded. The authoritative audit path runs the same preprocessing and final guards used by the Local Worker:

1. rembg + RTMLib guidance
2. Shading Flatten candidate (sr=45)
3. Shading Flatten Final Guard
4. Layered Person
5. Semantic Geometry Mass candidate
6. Geometry Mass final complexity guard
7. final PNG export with source-alpha preservation

The audit compares final pixel SHA for Geometry Mass OFF vs ON. Intermediate candidate acceptance is not counted as a changed case unless it survives all later guards and changes the final PNG.

## Approved-68 result

- expected cases: 68
- actual cases: 68
- missing: 0
- duplicates in final merge: 0
- errors: 0
- final PNG changed cases: 3
- total person-part polygon vertex savings: 37
- visible-shape increases in changed cases: 0

Changed cases:

- 12 Koseki Bijou, torso: 56 -> 32 vertices, 5 -> 5 visible shapes, 24 vertices saved.
- 27 Hakos Baelz, torso: 18 -> 11 vertices, 2 -> 2 visible shapes, 7 vertices saved.
- 47 Pavolia Reine, right_leg: 16 -> 10 vertices, 2 -> 2 visible shapes, 6 vertices saved.

All other 65 cases produced the same final pixel SHA with Geometry Mass OFF and ON.

## Interaction with Shading Flatten

Geometry Mass did not flip the Shading Flatten accept/reject decision in any of the 68 cases.

Two cases changed only the rejection-reason set:

- 13 Kobo Kanaeru: rejected in both paths.
- 47 Pavolia Reine: rejected in both paths.

Therefore Geometry Mass did not cause a Shading Flatten candidate that was previously rejected to become accepted, or vice versa.

## Changed-case Approved-reference diagnostics

The diagnostic metrics are secondary evidence, not the production guard itself.

Koseki Bijou:
- color similarity: +0.000203
- edge IoU: -0.005135
- changed pixels: 1,142
- visual review: the torso/face-adjacent jagged fragment is consolidated into a larger geometric plane.

Hakos Baelz:
- color similarity: +0.0000087
- edge IoU: unchanged
- changed pixels: 3
- visual review: effectively imperceptible, with lower polygon complexity.

Pavolia Reine:
- color similarity: +0.000414
- edge IoU: +0.000079
- changed pixels: 328
- visual review: a small dark-blue protrusion is removed. The Approved-reference diagnostics improve slightly, and visible shape count does not grow.

## Production policy

Library/API compatibility remains conservative:

- LayeredPersonConfig.semantic_geometric_mass default remains False.

Local Worker production path opts in explicitly:

- MINIMALIZER_LOCAL_GEOMETRIC_MASS defaults to 1.
- Set MINIMALIZER_LOCAL_GEOMETRIC_MASS=0 to roll back without changing code.
- /health reports semantic_geometric_mass.
- API responses expose X-Minimalizer-Geometry-Mass.

The Geometry Mass final guard remains mandatory. A candidate is never accepted when final visible-shape count grows, and it must produce real polygon-vertex savings.

## Evidence

- docs/handoffs/data/HND-20260926_geometry_mass_approved68_integrated_summary.json
- docs/handoffs/data/HND-20260926_geometry_mass_changed_vs_approved.json
- tools/audit_geometry_mass_integrated_postguard.py

Older pre-final-guard scans remain reference-only and must not be used as production evidence.
