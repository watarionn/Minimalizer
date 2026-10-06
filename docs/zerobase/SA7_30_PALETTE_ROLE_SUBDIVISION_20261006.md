# SA7.30 Palette-role / Composition-aware Macro Subdivision — 2026-10-06

Status: PALETTE ROLE CONTRACT PASS / VISUAL ADOPTION HOLD

SA7.30 adds a deterministic source-only palette-role observer for semantic parts. It clusters source pixels in Lab space into at most three dominant roles, then keeps only spatially coherent source-contained masses. Golden and Browser fallback v12 are evaluation references only and never enter inference.

GC001 source evidence:
- hair roles: orange dominant, light highlight, dark shadow
- major_clothing roles: pink/red dominant, light garment mass, dark garment mass

Experimental rendering over the rejected SA7.29 macro candidate:
- Visual Delta vs adopted baseline: 36.3676%
- candidate -> Golden LAB distance: 54.6792
- SA7.29 -> Golden LAB distance: 54.8153
- Browser fallback v12 -> Golden LAB distance: 16.2422
- candidate edge density: 0.03551
- v12 edge density: 0.04046

Palette-role subdivision recovers some internal structure and slightly improves the rejected SA7.29 candidate, but remains far below the v12 regression floor. Therefore the observer/IR is useful but the visual candidate is not adopted.

Next: SA7.31 Role-localized Golden Gap Attribution. Use Golden only in evaluation to measure which semantic source roles/regions dominate the remaining gap. Do not tune production geometry from Golden coordinates.
