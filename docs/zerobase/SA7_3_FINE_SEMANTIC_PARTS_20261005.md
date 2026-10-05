# SA7.3 Fine Semantic Part Decomposition — 2026-10-05

Status: FOUNDATION PASS / PRODUCTION-NEUTRAL / MERGE CANDIDATE

## Goal

Increase semantic resolution before geometry so required identity is represented explicitly rather than guessed by the renderer.

Fine identity categories:

- eyewear
- headwear
- hair_front
- hair_side
- collar
- tie_or_neckwear
- major_accessory

## Implementation

`fine_part_decomposition.py` adds two separate stages:

1. deterministic observer proposals from source pixels + coarse semantic masks;
2. semantic promotion under an existing non-suppressed parent authority.

Observer evidence is not semantic authority.

Promotion validates:

- category allowlist,
- confidence,
- parent existence and policy,
- parent/composite authority containment,
- category-specific parent area ratios,
- anatomical upper-face proximity for eyewear.

Eyewear/headwear may use composite `head | hair` authority because worn head structures legitimately cross the coarse head/hair boundary.

Unknown proposals are not silently promoted.

## Verification

- focused fine-part tests: 7 PASS
- full ZeroBase: 514 PASS
- git diff --check: PASS
- no renderer integration in this stage
- therefore no production visual behavior change and no visual adoption claim

## GC001 evidence-only validation

The unchanged observer/promotion rules produce and promote:

- eyewear, confidence 0.8924
- hair_front, confidence 0.82
- hair_side, confidence 0.78
- tie_or_neckwear, confidence 0.72
- collar, confidence 0.62
- major_accessory, confidence 0.90

The eyewear proposal passes composite `head | hair` authority validation with zero pixels outside that authority.

This is the first semantic-abstraction stage where the GC001 goggles exist as an explicit `eyewear` SemanticPart before rendering.

## Important limitation

Bounding boxes on the debug board show semantic extent, not exact render geometry. The eyewear evidence still includes multiple source-supported components and must be converted by a category-specific geometry grammar in the next stage.

SA7.3 must not render these boxes directly.

## Next: SA7.4 Fine-Part Geometry Grammar

- consume explicit fine SemanticParts
- category-specific primitive grammar
- eyewear: bounded frame/lens components, not one giant hull
- hair_front/hair_side: separate coarse masses
- collar/tie: topology-aware clothing primitives
- major_accessory: preserve required minimum
- reserve fine-part primitive minimums before macro masses
- keep face internals suppressed
- unchanged hard gates
- actual four-way + chronological version history before visual adoption
