# HND-20261006 Minimalizer PB4 / SA4 Semantic Debug Board Backport

Date: 2026-10-06
Status: PB4 COMPLETE / SUPERSEDED BY PB5 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-pb5-sa5-face-neutralization-compatibility-audit-next.md`.

PB3 implementation:
- PR #184
- merge SHA: `fd62415a42f881d0b70a0177f2d2f73a1143624e`

Canonical PB3 record:
`docs/zerobase/PB3_SA3_IMPORTANCE_POLICY_BACKPORT_20261006.md`

PB3 Drive evidence:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB3_SA3_20261006`

Folder ID:
`1CTmoWD703YNyiGhw60YH1TlAJws_L4tY`

## PB3 closure

Classification:
**IMPLEMENTED + OBSERVER/ADVISOR-ONLY**

GC001:
- components: 83
- context semantic retention: 0.7298672763136121
- per-component semantic perturbation observer: unavailable
- primitive advisor: unavailable
- retain-evidence: 0
- merge-candidate-evidence: 0
- omission-candidate-evidence: 0
- insufficient-evidence: 83
- production actions: 0
- existing SA7.44 candidate SHA unchanged

Verification on exact merged implementation main `fd62415a42f881d0b70a0177f2d2f73a1143624e`:
- focused PB3 + importance/omission: 27/27 PASS
- ZeroBase: 701/701 PASS
- compileall: PASS
- git diff --check: PASS

## PB4 / SA4 Semantic Debug Board Backport — COMPLETE

Primary precedents:
- CLIPasso / CLIPascene
- SuperSVG
- LayerPeeler

### Goal

Build a canonical inspectable debug/evaluation board for PB2/PB3 evidence so a human can see:
- what source components/layers were observed;
- which evidence is semantic-observer vs advisor vs production authority;
- whether removal/merge semantic impact is available or unavailable;
- why a PB3 diagnostic recommendation was emitted;
- which hard safety state remains authoritative.

PB4 is a diagnostic/UI artifact layer.

It must not change production geometry, palette, z-order, importance, omission, or rendering.

### Existing assets to reuse

PB2:
- stable component IDs;
- component support ratios;
- role counts;
- OVERLAP / TOUCHING / DISJOINT relation evidence;
- observed/advisor/promoted authority provenance.

PB3:
- per-component recommendation;
- semantic retention;
- removal impact;
- merge impact;
- primitive advisor context;
- reasons;
- explicit production_action=null.

SA7.45:
- overall semantic-retention context.

SA7.47:
- layer relationship semantics.

### Preferred output model

PB4 should create a machine-readable debug-board payload plus a deterministic renderable board specification.

Per component row/card:
- component ID;
- role;
- source support;
- evidence authority state;
- semantic observer availability;
- removal impact;
- merge impact / merge target;
- primitive advisor status/agreement;
- PB3 recommendation;
- recommendation reasons;
- production action;
- hard-failure override allowed = false.

Role/layer summary:
- component counts;
- relation counts;
- high-identity role flags;
- observer availability counts;
- recommendation counts.

Global summary:
- semantic context score;
- hard failures;
- production policy changed = false;
- production output changed = false;
- adopted visual baseline unchanged.

### Visual principles

The debug board is engineering evidence, not a decorative product UI.

Prefer:
- compact tables;
- direct labels;
- explicit status text;
- clear source/component linkage;
- deterministic sorting.

Avoid:
- glossy card styling;
- hidden hover-only explanations;
- ambiguous color-only states;
- AI-template ornament.

### Authority display

Every board must visibly separate at least:

1. OBSERVED EVIDENCE
2. ADVISOR EVIDENCE
3. PROMOTED PRODUCTION AUTHORITY

PB2/PB3 evidence should remain in the first two categories.

If no promoted authority exists, show count = 0 explicitly.

### Required tests

1. deterministic board payload ordering;
2. mapping/input-order invariance;
3. every PB3 component represented exactly once;
4. recommendation reasons preserved;
5. observer unavailable visibly represented;
6. advisor unavailable visibly represented;
7. hard-failure state cannot be hidden by a high quality score;
8. production action remains null for PB3 diagnostics;
9. board generation does not mutate PB2/PB3 inputs;
10. board generation does not change ImportanceEngine or Phase 8 omission outputs.

### GC001 expected board

PB4 should make the current GC001 state obvious:

- 83 observed components;
- 83 insufficient-evidence recommendations;
- semantic context exists globally;
- per-component semantic perturbation evidence is unavailable;
- primitive advisor is unavailable;
- production authority count = 0;
- production action count = 0.

The board should explain that this is a fail-safe state, not a failure to process the image.

### Hard boundaries

- no production rendering change;
- no Golden/v12 production authority;
- no semantic recommendation promotion;
- no hidden aggregation that masks hard failures;
- no generative redraw;
- no arbitrary external HTML/SVG execution;
- deterministic machine-readable payload remains canonical even if a visual board renderer is later added.

### Preferred implementation order

1. Define PB4 board schema.
2. Convert PB2 + PB3 report into deterministic board rows.
3. Preserve authority categories explicitly.
4. Add role/relation/recommendation summaries.
5. Add global hard-safety summary.
6. Add deterministic text/JSON renderer first.
7. Add a simple static visual board only if the schema is already verified.
8. Run focused tests.
9. Run full ZeroBase.
10. Generate GC001 board.
11. Preserve to Drive.
12. Classify PB4 before PB5.

## Expected classification

**IMPLEMENTED + DIAGNOSTIC-ONLY**

## After PB4

PB5 / SA5 Face Neutralization Compatibility Audit.

PB5 should not replace the SA7.38 face raster safety contract. It should only check whether precedent-derived observer/debug layers can coexist without weakening Forbidden Face Detail = 0.00%.

## Current state declaration

The canonical continuation point is:

**PB5 / SA5 Face Neutralization Compatibility Audit**
