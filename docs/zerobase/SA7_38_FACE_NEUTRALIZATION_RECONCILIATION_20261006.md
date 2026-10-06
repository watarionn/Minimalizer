# SA7.38 Face Neutralization Path Reconciliation — 2026-10-06

Status: CANONICAL FACE SAFETY RESTORED / VISUAL ADOPTION HOLD

SA7.38 reconciles the face-neutralization mismatch uncovered by SA7.35.

## Root cause

SA7.2 produced a completely flat face-mask raster:

- face pixels: 4,937
- dominant/only color: one flat color
- Forbidden Face Detail: 0.0000%

SA7.29 and later candidates contained multiple rendered head/identity layers inside the same semantic face mask:

- white head/identity layer dominated the face area;
- older orange head pixels remained in several components;
- fresh image-level Forbidden Face Detail: 14.4622%.

The semantic policy-level face gate was still PASS because facial-feature SemanticParts were suppressed, but that policy result did not guarantee a flat final raster. The failure therefore existed between semantic policy and final rendered pixels.

## Rejected scene-only repairs

### Exact face polygon

The Phase-4 face mask can be represented exactly by one 110-vertex OpenCV polygon with 100% mask coverage and zero mask spill.

However, when rendered as SVG in Chrome, pixel-coverage rules left a thin set of old head-layer pixels visible inside the face mask:

- face detail ratio: about 2.29%.

### SVG stroke expansion

A same-color 1.5px stroke reached 0.0000% face detail, but changed 161 pixels outside the face mask.

That spill intersected other semantic roles, including hair, torso, clothing, neck, and unknown regions. The stroke approach was rejected.

## Adopted SA7.38 contract

SA7.38 adds a deterministic post-render face raster safety guard.

Inputs:
- current rendered RGB
- original source RGB
- authorized semantic face mask

Forbidden inputs:
- Golden raster
- adopted-baseline pixels as repair authority
- facial-feature proposals
- generative reconstruction/inpainting
- case-specific coordinates/colors

Algorithm:
1. collect source pixels inside the semantic face mask;
2. compute the source-face median only as a robust target statistic;
3. choose the actually observed source pixel nearest that median;
4. copy the rendered image;
5. replace exactly the authorized face-mask pixels with that observed source color;
6. assert that zero pixels outside the face mask changed.

The guard is deterministic and does not invent image content.

GC001 observed fill:
- RGB [250,225,218]
- face pixels: 4,937
- changed outside face: 0

## Combined GC001 result

SA7.38 is evaluated on top of the SA7.37 research reservation candidate.

Fresh canonical SA7.35 hard gate:

- required signatures: 16
- Feature Survival: missing=0 — PASS
- Forbidden Face Detail: 0.0000% — PASS
- overall canonical hard gate: PASS

This is the first SA7.29-family candidate after reconciliation that simultaneously restores:
- source-supported Feature Survival;
- exact image-level face neutralization.

## Visual evidence

- Visual Delta vs adopted baseline: 71.4429%
- change vs SA7.37: 4.2708%
- SA7.37 -> Golden LAB MAE: 32.6883
- SA7.38 -> Golden LAB MAE: 32.3803
- Browser fallback v12 -> Golden LAB MAE: 16.2422

The face guard slightly improves Golden distance while restoring all canonical hard gates.

LAB remains supporting evidence only, not the sole v12-floor authority. Actual four-way review remains required.

## Decision

Merge:
- deterministic face raster guard;
- reproducible guard CLI;
- focused/full regression tests.

Do not merge the rejected scene-polygon/stroke experiment.
Do not update the adopted visual baseline.
Do not append SA7.38 to accepted Minimalizer Version History because the Browser fallback v12 regression floor is still not beaten.

## Next

SA7.39 Required Semantic Mass Canonical Integration.

SA7.37 currently proves the reservation policy via a research raster overlay. Integrate the source-only required semantic masses into the canonical scene/output path so the combined SA7.37 + SA7.38 PASS no longer depends on an evaluation-only raster overlay.
