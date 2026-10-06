# PB3 / SA3 Importance & Policy Backport — 2026-10-06

Status: IMPLEMENTED + OBSERVER/ADVISOR-ONLY

Primary precedents:
- CLIPasso
- CLIPascene
- StarVector advisor

## Goal

Backport semantic-retention and primitive-advisor knowledge into the importance/policy layer without changing existing production keep/protect/prune behavior.

PB3 adds a diagnostic layer that answers:

- what source support a PB2 component has;
- whether a real semantic observer reports removal impact;
- whether a real semantic observer reports merge impact;
- what semantic/identity role context already exists;
- whether a primitive advisor agrees with deterministic source geometry;
- whether evidence is observed/advisor-only or promoted authority;
- whether there is enough evidence to recommend retain/merge/omission review.

Recommendations are evidence, never production actions.

## New module

`minimalizer_zerobase/importance/precedent_diagnostic.py`

Contract version:
`pb3-v1`

New public contracts:
- `PB3Recommendation`
- `ComponentImportanceDiagnostic`
- `PB3ImportanceDiagnosticReport`
- `build_pb3_importance_diagnostic(...)`

Exported from:
`minimalizer_zerobase.importance`

## Inputs

PB3 consumes:

1. PB2 `region_component` Evidence;
2. optional component-removal `SemanticRetentionReport`;
3. optional component-merge `SemanticRetentionReport`;
4. optional StarVector-style `PrimitiveAdvisorReport`;
5. optional overall semantic-retention context;
6. existing hard-failure labels as diagnostic context.

PB3 does not analyze pixels itself.

## Component dimensions

Per PB2 component, PB3 records:

- stable component ID;
- semantic role;
- source support ratio;
- same-role sibling count;
- existing semantic-role importance;
- existing identity-role importance;
- observed semantic retention after removal, when supplied;
- removal impact = `1 - semantic_retention`;
- observed semantic retention after merge, when supplied;
- merge impact = `1 - semantic_retention`;
- explicit merge target ID;
- primitive advisor status;
- primitive advisor agreement;
- suggested primitive family;
- deterministic source primitive family;
- diagnostic recommendation;
- reasons;
- authority state;
- `production_action = null`.

## Recommendation vocabulary

PB3 exposes exactly four diagnostic recommendations:

- `retain-evidence`
- `merge-candidate-evidence`
- `omission-candidate-evidence`
- `insufficient-evidence`

These values are not Phase 8 actions.

They do not map automatically to:
- protect;
- keep;
- prune;
- geometry family changes.

A separate explicit deterministic promotion rule would be required later.

## Semantic-impact safety contract

PB3 never estimates semantic removal impact from area/support alone.

If neither removal nor merge semantic observation exists:
- recommendation = `insufficient-evidence`

Observed removal impact:
- semantic-retention score is converted to `1 - retention`;
- a high observed semantic loss produces `retain-evidence`.

Omission-candidate evidence requires all of:
- a real per-component semantic-removal observation;
- very low observed semantic impact;
- low source support;
- another same-role component;
- not a high-identity role.

Merge-candidate evidence requires:
- a real merge semantic observation;
- an explicit merge target;
- very low merge semantic impact;
- another same-role component.

Area alone is never sufficient.

## Identity guard

Existing Phase 8 identity-role priors are reused as diagnostic context.

A high-identity role cannot become omission-candidate evidence merely because:
- it is tiny;
- an advisor has high confidence;
- a general semantic context score is high.

Synthetic tests confirm tiny hair remains `retain-evidence` even with a very low measured removal impact because hair is high-identity context.

## Primitive advisor boundary

PB3 may attach StarVector-style advisor evidence:
- status;
- suggested family;
- deterministic source family;
- family agreement.

The advisor does not:
- create semantic-removal evidence;
- create merge evidence;
- create a production action;
- change geometry;
- change renderer family.

A perfect-confidence advisor with no semantic-impact evidence still yields `insufficient-evidence`.

## Hard-failure boundary

PB3 reports:
- `authoritative=false`
- `can_override_hard_fail=false`
- all supplied hard failures unchanged

Synthetic verification proves that even semantic retention = 1.0 cannot clear a hard failure.

## Production policy no-op

PB3 is separate from:
- `ImportanceEngine`;
- `evaluate_importance_omission`.

A dedicated regression test snapshots both production surfaces, generates PB3 diagnostics, and verifies their outputs remain byte/data-identical afterward.

PB3 report fields also explicitly state:
- `production_policy_changed=false`
- `production_output_changed=false`

## Verification

Focused PB3 + existing importance/omission:
- **27/27 PASS**

Full ZeroBase:
- **701/701 PASS**

Other:
- Python compileall: **PASS**
- git diff --check: **PASS**

Focused verification covers:
- unavailable semantic observer does not infer omission from area;
- high observed removal impact -> retain evidence;
- real low-impact small low-identity component -> omission-candidate evidence;
- high-identity guard;
- explicit low-impact merge -> merge-candidate evidence;
- merge target requirement;
- primitive advisor cannot act alone;
- perfect semantic score cannot clear hard failure;
- authoritative semantic report fail-closed;
- unknown component fail-closed;
- promoted PB2 Evidence rejected as observer input;
- ImportanceEngine no-op;
- Phase 8 omission no-op.

## GC001 real diagnostic

PB2 structured components:
- **83**

Existing overall SA7.45 DINO semantic context:
- candidate semantic retention: **0.7298672763136121**

StarVector-style primitive advisor:
- status: **UNAVAILABLE**
- local StarVector runtime/model was not installed during SA7.46

Per-component semantic removal/merge observer artifacts:
- **UNAVAILABLE**

Therefore PB3 refuses to invent semantic removal/merge impact.

GC001 recommendation counts:
- retain-evidence: 0
- merge-candidate-evidence: 0
- omission-candidate-evidence: 0
- insufficient-evidence: **83**

This is the intended fail-safe result.

The fact that some PB2 components are tiny is not treated as evidence that they are semantically disposable.

## Production integrity

Existing SA7.44 GC001 production candidate SHA-256 was measured before and after PB3 diagnostic generation.

Result:
- unchanged: **true**

Production actions generated:
- **0**

Hard-fail override:
- **false**

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB3_SA3_20261006`

Folder ID:
`1CTmoWD703YNyiGhw60YH1TlAJws_L4tY`

Verified cloud artifacts:

- `GC001_pb3_importance_diagnostic.json`
  - `1ytdKU8t-H_7TRMSB9k2RGhfruMM98V9y`
- `GC001_pb3_importance_diagnostic_board.png`
  - `1aqwEu66Df9lYW32BFZNZVWKrImPdg1Fc`

## Classification

**IMPLEMENTED + OBSERVER/ADVISOR-ONLY diagnostic expansion**

PB3 is complete.

The most important architectural result is that Minimalizer now has an explicit place to ask:
"what semantic evidence says this can disappear?"

and an equally explicit answer when that evidence does not exist:
"insufficient evidence, do not infer from size."

## Next

PB4 / SA4 Semantic Debug Board Backport.

Primary precedents:
- CLIPasso / CLIPascene
- SuperSVG
- LayerPeeler

Goal:
turn PB2/PB3 evidence into an inspectable debug board that shows why each component was observed, why its semantic-impact state is available/unavailable, what any advisor proposed, and why the current diagnostic recommendation was emitted, while clearly separating observer evidence from production decisions.
