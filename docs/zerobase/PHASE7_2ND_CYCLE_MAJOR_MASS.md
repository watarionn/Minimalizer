# Phase 7 — Major Mass Reconstruction

Status: CLOSED / PASS

Date: 2026-09-28

## Goal

Convert Phase 6 semantic regions into larger readable masses without repairing or overriding upstream semantic uncertainty.

Phase 7 is the first ZeroBase 2nd Cycle visual stage implemented directly on top of the common Artifact Contract provenance chain.

## Canonical rule

Phase 7 v1 merges regions only when all of the following are true:

- both regions are Phase 6 `bound`
- both have the same `semantic_part_id`
- they are adjacent in the Phase 6 region graph
- shared boundary pixels satisfy the configured minimum

Cross-part merge is forbidden in v1.

Unbound regions are never absorbed into a bound mass and are never merged with each other.


This is intentionally stricter than the general design allowance that a cross-part merge may be possible with an explicit structural relation. Relation-aware cross-part merging is deferred until a concrete case requires it and can be separately gated.

## Inputs

Read-only inputs:

- canonical source image
- Phase 6 `06_region_bindings.json`
- Phase 6 `06_region_labels.png`
- Phase 6 `metrics.json`
- Phase 6 `stage.json`

The reconstruction consumes Phase 6 pixel runs, region adjacency, binding status, and semantic ownership.

It does not rerun segmentation and does not call an analyzer.

## Outputs

Mandatory Phase 7 artifacts:

- `07_masses.json`
- `07_mass_labels.png`
- `07_mass_silhouette.png`
- `07_mass_blocks.png`
- `07_mass_outline_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`


`07_masses.json` contains semantic mass records, region membership, pixel runs, source-derived mean RGB, and a part-to-mass hierarchy.

`07_mass_silhouette.png` is the exact union of Phase 6 region pixels. It adds no pixels and performs no hole filling or hidden-region completion.

`07_mass_blocks.png` uses source-derived mean RGB per bound mass. Unbound masses remain the fixed diagnostic magenta. The background is a fixed light neutral to keep dark hair/clothing readable during QA.

## Structural validation

Phase 7 fails closed on:

- duplicate or invalid Phase 6 region records
- pixel-run bounds errors
- pixel-count mismatch
- overlapping Phase 6 pixel ownership
- missing adjacency targets
- non-reciprocal adjacency
- shared-boundary disagreement
- mixed bound/unbound mass membership
- cross-semantic-part mass membership
- lost subject pixels
- claimed pixels outside the Phase 6 subject

The Phase 6 input payload is treated as read-only and is not mutated.


## Diagnostic-2

### Hyakuto-Kyoko

- Phase 6 regions: 476
- Phase 7 masses: 201
- bound masses: 171
- preserved unbound masses: 30
- region-to-mass reduction: 0.577731
- subject pixel coverage: 1.0
- cross-part merge count: 0
- unbound absorbed into bound: 0
- structural gate: PASS
- provenance artifacts: 42
- provenance gate: PASS

Visual QA: PASS. The filled mass view retains the head/hair envelope, face placement, upper-body pose, arm placement, long hair silhouette, and green tie/major accessory cues. Existing Phase 6 unbound fragments remain visibly magenta rather than being silently reassigned.

### Juufuutei-Raden

- Phase 6 regions: 334
- Phase 7 masses: 93
- bound masses: 55
- preserved unbound masses: 38
- region-to-mass reduction: 0.721557
- subject pixel coverage: 1.0
- cross-part merge count: 0
- unbound absorbed into bound: 0
- structural gate: PASS
- provenance artifacts: 42
- provenance gate: PASS


Visual QA: PASS. The filled mass view retains long hair, face placement, torso and large sleeve masses, raised-arm pose, rod silhouette, and the major decorative cluster. Phase 6 uncertainty around accessory/detail fragments remains magenta and is not repaired downstream.

## Determinism

Final Phase 7 rerun:

- Hyakuto-Kyoko: 8 / 8 artifact SHA matches
- Juufuutei-Raden: 8 / 8 artifact SHA matches

## Provenance

Phase 7 extends the Stage Contract Bridge with `max_phase=7`.

Run IDs:

- `Hyakuto-Kyoko:phase03-07`
- `Juufuutei-Raden:phase03-07`

Hyakuto-Kyoko final hashes:

- `run.json`: `2712c0dcdd4b072c517ac3b6bb65f2a68c92e7d02931c39328368e6e803db9c8`
- `artifacts.json`: `472e480f0c5b54f202e693df94d88ec823cc8546fb6e17b9687155d087fad917`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`


Juufuutei-Raden final hashes:

- `run.json`: `85196bb1a30f90a002670ec07f3972fbaffe3a0e23ddb244cd75982c462be412`
- `artifacts.json`: `6f20bf83d32b10fd2f1221ce8352d5227774ac9280ff5af7bf6f91cedb1dc419`
- `provenance_gate.json`: `340ccdaa5f444f076f797c11f41471969bedbd938d9e5177f9829fd2682e9af1`

## Safety boundary

Phase 7 does not:

- generate or inpaint pixels
- complete invisible geometry
- change Phase 3-6 artifacts
- override Phase 6 semantic ownership
- give analyzer output final render authority
- change Minimalizer 2.0 production routing

The output is a deterministic restructuring of observed source pixels only.

## Tests

Focused Artifact Contract + Bridge + Phase 7: 34 passed.

Full ZeroBase suite: 132 passed.

Existing local merge-readiness: PASS.

- Stable/Web regressions: 131 passed
- Phase 16 corpus gate: PASS
- real-server smoke: PASS
- final marker: `LOCAL_MERGE_VALIDATION_PASS`

## Next phase

Phase 8 Importance / Omission Policy may consume Phase 7 masses, but it must not reinterpret an unbound Phase 6/7 mass as a known semantic part merely to simplify the image.
