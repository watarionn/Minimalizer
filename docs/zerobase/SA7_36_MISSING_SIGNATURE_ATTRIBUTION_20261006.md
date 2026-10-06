# SA7.36 Missing Signature Semantic Attribution — 2026-10-06

Status: ATTRIBUTION CONTRACT PASS / REPAIR NEXT

SA7.36 converts the three canonical SA7.35 missing feature signatures into source-supported semantic evidence.

## Contract

Inputs:
- canonical SA7.35 missing signatures
- original source image
- Phase 3 subject mask
- Phase 4 semantic masks

Golden is not an input.

The evaluator first verifies source support under the same feature-signature metric used by the canonical hard gate. It then searches connected quantized-color components in the source rather than relying on one aggregate color centroid.

To resist tiny disconnected noise, a component must contain at least:
- 4 pixels, and
- 10% of the missing signature's implied subject-area size.

The closest surviving component is intersected with all semantic masks. Overlap evidence is preserved even when masks overlap; attribution does not force exclusive semantic ownership.

## GC001 results

### Missing signature 1

- canonical signature: RGB [16,16,16]
- connected source component: 399 px
- component distance: 0.01245
- torso overlap: 379 / 399 = 94.99%
- major_clothing overlap: 18 / 399 = 4.51%
- hair overlap: 2 / 399 = 0.50%
- primary semantic evidence: torso

### Missing signature 2

- canonical signature: RGB [16,48,48]
- connected source component: 34 px
- component distance: 0.01380
- right_arm overlap: 34 / 34 = 100%
- primary semantic evidence: right_arm

### Missing signature 3

- canonical signature: RGB [144,176,16]
- connected source component: 72 px
- component distance: 0.00060
- torso overlap: 60 / 72 = 83.33%
- major_clothing overlap: 12 / 72 = 16.67%
- primary semantic evidence: torso with secondary clothing overlap

## Interpretation

The current hard-gate regression is no longer an anonymous missing=3 problem.

The missing source-supported evidence clusters into:
- two torso-associated semantic masses;
- one right-arm semantic mass.

This does not authorize hard-coded GC001 colors, coordinates, or masks in production. The attribution is evaluation evidence that identifies which semantic roles need stronger survival policy.

## Decision

Merge the generic connected-source attribution evaluator and reproducible CLI.

Do not alter the adopted visual baseline.

## Next

SA7.37 Required Semantic Mass Reservation.

Reserve a bounded amount of source-supported geometry for required torso/limb semantic masses before macro compression. The rule must be semantic-role-based and validated on synthetic non-GC001 cases before GC001.
