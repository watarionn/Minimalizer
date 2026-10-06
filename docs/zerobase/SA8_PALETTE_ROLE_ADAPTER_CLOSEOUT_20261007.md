# SA8 Palette Role Adapter Closeout — 2026-10-07

Status: **SA8 COMPLETE / IR + BRIDGE PRESERVED / RENDERER PROMOTION HOLD / SA9 NEXT**

## What SA8 established
- palette-role identity is distinct from connected-component identity;
- one palette role can preserve multiple disconnected source fields;
- palette-role budget and primitive budget are independent;
- PB2 component evidence can feed palette-role IR without becoming semantic/anatomy authority;
- source-only deterministic candidate bridge exists and is tested;
- Golden and Browser fallback v12 remain evaluation-only.

## Renderer promotion experiments
All fresh GC001 runs kept Golden/v12 out of inference and passed the canonical hard gate with 16/16 required signatures, missing=0, Forbidden Face Detail 0.00%.

- SA8 direct palette-role candidate pass: Golden Lab 92.8560, HOLD.
- SA8.1 bounded coverage-gain overlay: Golden Lab 95.3020, HOLD.
- SA8.2 downstream-compatible overlay: Golden Lab 94.6476, HOLD.
- SA8.3 palette evidence inside existing perceptual budget: Golden Lab 95.1963, HOLD.
- Same-run SA7.44 reference in these runs: Golden Lab 51.4763.
- Same-run Browser fallback v12 evaluation floor: Golden Lab 33.4426.

Therefore no tested SA8 renderer promotion is justified.

## Canonical production decision
Keep on main:
- Palette Role Adapter IR;
- SA7.30 compatibility path that does not collapse a palette role to its largest island;
- source-only palette-role production-candidate bridge;
- independent palette/primitive budgets;
- tests and authority boundaries.

Do not activate on main:
- dedicated SA8 renderer pass;
- bounded secondary overlay;
- downstream-compatible overlay;
- perceptual-budget SA8 injection.

The failed visual experiments remain in closed, unmerged PRs #193, #194, #195 as evidence.

## Authority
SA8 does not gain anatomy, topology, z-order, face, or hard-gate override authority. Existing deterministic renderer and hard guards remain canonical.

## Process rule confirmed
Any visual-authority promotion must pass real GC001 visual-floor review before merge. Synthetic/full tests are necessary but not sufficient.

## Next
Proceed to SA9 according to the adopted precedent-assimilation plan. Do not spend another SA8 cycle tuning renderer thresholds unless SA9 or later evidence creates a new justified integration point.
