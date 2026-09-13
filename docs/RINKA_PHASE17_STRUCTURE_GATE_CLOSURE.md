# Rinka Reference Phase 17: Structure Gate Closure

Phase 17 changes the Approved Reference prototype from color-first reconstruction to structure-first reconstruction. Production remains Phase 16; this document records the experimental closure state only.

## Final experimental order

`source image -> subject mask arbitration -> face locator -> face-seeded/sleeve recovery -> structure partition -> silhouette head/hair -> body planes -> carrier guard -> candidate gate`

The key rule is that color follows structure. Color clustering no longer decides the outer body layout.

## Approved 18 result

The exact 18 source images and the 18 user-approved geometric references were used as the fixed visual regression set.

Final structure-gate audit: **18 / 18 PASS**.

The final gate requires:
- structure, face, head, and alpha-structure stages to succeed;
- 1 to 3 coarse hair planes;
- exactly one blank face plane;
- at least two body-zone planes;
- no full-size carrier;
- carrier exposure <= 0.30;
- carrier patches <= 6;
- structural shape count between 4 and 12, excluding carrier patches.

Body residual pixels are absorbed into the nearest left-sleeve / torso / right-sleeve zone before polygonization. This is what removed the previous 30-40% carrier-exposure failures without relaxing the carrier gate.

## Auxiliary corpus evidence

On the 16-image repository corpus, the final candidate gate passes all 15 character images and rejects the non-character Night River image. The maximum carrier exposure falls to about 0.206 after body-residual absorption.

Hair remains intentionally coarse. Connected hair structure is preserved as at most three planes, using front / side / back-style components instead of forcing a vertical split through continuous hair.

Structure Voronoi remains gated. Approved-18 audit accepts it on 14/18 and deliberately falls back on the other four cases rather than forcing unstable arm/torso assignments.

## Safety state

Phase 17 is still shadow/comparison-only. It does not replace the Phase 16 production renderer. No GitHub Actions should be triggered while metered Actions could incur charges; local validation is the closure evidence.

## Local closure validation

Final local checks on 2026-09-13:
- Phase 17 / target-style focused regression: 75 / 75 passed
- repository-wide pytest: 322 passed / 2 known missing-fixture failures
- both failures require the pre-existing absent `tests/assets/false_face_phase85.png`
- `python -m compileall -q minimalize_engine web`: passed
- `node --check web/static/app.js`: passed
- `git diff --check`: passed

No new Phase 17 regression was found by the repository-wide suite.
