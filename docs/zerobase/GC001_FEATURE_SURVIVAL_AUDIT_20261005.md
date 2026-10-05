# GC001 Feature Survival Audit — 2026-10-05

## Purpose
Trace the identity-accent regression observed after Perceptual Region Budget without adding GC001-specific production heuristics.

## Result
The green identity accent is **not lost by Phase4 semantic ownership**. A diagnostic vivid-green predicate finds 1,707 source pixels, and all 1,707 remain inside the union of Phase4 masks.

Relevant Phase4 overlap:
- torso: 104 green pixels
- major_clothing: 76 green pixels
- accessory_or_held_object: 0 green pixels

Connected green evidence exists inside torso (largest component 47 px) and major_clothing (largest component 49 px).

The loss occurs later: edge-aware region proposals for torso and major_clothing produce no proposal whose representative RGB remains green, even when inspecting 20 proposals per part. The evidence is being absorbed into neighboring superpixels and their representative colors before perceptual budgeting.

## Decision
Do not tune the budget to rescue GC001. The budget cannot preserve a feature that the proposal stage no longer represents.

Next engineering target: **contrast-preserving proposal representation**. A compact high-contrast subregion must be able to survive superpixel aggregation as its own candidate or protected subregion, while semantic masks remain the authority.

## Guardrails
- Diagnostic green predicates are audit-only and MUST NOT enter production.
- No Golden image is used as reconstruction input.
- No GC001 coordinates, green-tie rule, or character-specific labels in production.
- Browser fallback v12 remains the regression baseline.
