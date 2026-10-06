# HND-20261006 Minimalizer PB3 / SA3 Importance & Policy Backport

Date: 2026-10-06
Status: PB3 COMPLETE / SUPERSEDED BY PB4 HANDOFF
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

This handoff is now historical. For current work, restart from current `main` and read `docs/handoffs/HND-20261006-pb4-sa4-semantic-debug-board-backport-next.md`.

PB2 implementation:
- PR #183
- merge SHA: `cbaf8d87e84bdf2db558cff0c861edb831f05280`

Canonical PB2 record:
`docs/zerobase/PB2_SA2_EVIDENCE_ADAPTER_BACKPORT_20261006.md`

PB2 Drive evidence:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB2_SA2_20261006`

Folder ID:
`1TByZuKDRECM0CngUrN58vF3n8UAHHQ0I`

## PB2 closure

PB2 moved structured component/layer observation down into the SA2 analyzer boundary.

GC001:
- roles: 8
- connected components: 83
- layer relations: 28
- total observer Evidence: 111
- authority state: observed=111
- production authority: 0
- existing SA7.44 candidate SHA unchanged

Verification on exact merged main:
- ZeroBase: 689/689 PASS
- compileall: PASS
- git diff --check: PASS

Classification:
**IMPLEMENTED + OBSERVER-ONLY**

## PB3 / SA3 Importance & Policy Backport — COMPLETE

Primary precedents:
- CLIPasso
- CLIPascene
- StarVector advisor

### Goal

Add inspectable semantic-retention and removal/merge-impact evidence to the importance/policy layer without allowing observer/advisor scores to become a lone production keep/prune or primitive decision.

PB3 should answer questions such as:

- If this PB2 component disappears, does source-relative semantic identity materially change?
- If two components merge, is semantic retention stable?
- Does an external primitive-family suggestion agree with deterministic source geometry?
- Is a recommendation observer evidence, advisor evidence, or promoted deterministic authority?

### Existing implementation surfaces

Primary existing importance surfaces:

`minimalizer_zerobase/importance/engine.py`
- `ImportanceEngine`
- advisory tiers: disposable / preserve / protect
- consumes canonical Scene/Region/Subject

`minimalizer_zerobase/importance/omission.py`
- protect / keep / prune policy
- explicit silhouette, part-role, identity, salience, redundancy dimensions
- pruning already requires multiple independent low-value grounds and same-part redundancy evidence

Existing precedent assets:

From PB2:
- stable component identities
- component support ratio
- overlap/contact/disjoint evidence
- explicit observed/advisor/promoted authority trace

From SA7.45:
- generic `SemanticRetentionReport`
- global / patch / optional role-local retention
- observer cannot override hard failures

From SA7.46:
- non-authoritative primitive-family advisor audit
- deterministic source-geometry baseline
- advisor suggestions never production eligible by default

### Preferred PB3 architecture

PB2 component evidence
+ optional frozen semantic observations
+ optional primitive advisor audit
-> PB3 Importance Diagnostic
-> semantic contribution / removal impact / merge impact
-> recommendation evidence
-> existing Importance/Omission hard policy remains authoritative

PB3 should initially remain observer/advisor-only.

Do not directly alter existing keep/protect/prune outcomes until a separate deterministic promotion rule is proven with focused regressions.

### Suggested report dimensions

Per component / region where evidence is available:

1. source support ratio
2. current structural/semantic role importance
3. semantic retention if present
4. estimated removal impact
5. estimated merge impact
6. identity-local retention
7. redundancy context
8. primitive advisor agreement
9. authority state
10. recommendation:
   - retain-evidence
   - merge-candidate-evidence
   - omission-candidate-evidence
   - insufficient-evidence

Recommendations are evidence, not production actions.

### Removal / merge impact contract

Preferred first implementation is observation-driven and fail-safe.

Removal impact:
- compare frozen source/candidate semantic evidence where a real observer artifact exists;
- otherwise mark unavailable;
- do not invent semantic loss from area alone.

Merge impact:
- may use source support + PB2 relation/redundancy evidence;
- semantic observer evidence is optional;
- unavailable semantic observer must not cause a prune.

A perfect semantic score must never override:
- required feature survival;
- face safety;
- anatomy/topology;
- source-authority rules;
- silhouette hard guards;
- existing Phase 8 protection rules.

### Primitive advisor contract

StarVector-style primitive suggestions remain advisor-only.

PB3 may attach:
- suggested family
- source geometry family
- agreement
- confidence
- provenance

PB3 must not:
- execute generated SVG/code;
- change production geometry family;
- treat confidence as semantic truth.

### Preferred implementation order

1. Inventory current importance and omission schemas/tests.
2. Define a PB3 diagnostic report separate from production actions.
3. Bind PB2 stable component IDs into PB3 reports.
4. Reuse SA7.45 semantic-retention contract.
5. Reuse SA7.46 primitive-advisor audit.
6. Add deterministic recommendation categories that remain non-authoritative.
7. Test unavailable observer/advisor paths.
8. Test that perfect PB3 diagnostic evidence cannot rescue existing hard failures.
9. Test that PB3 generation does not change current ImportanceEngine / omission outputs.
10. Run focused + full ZeroBase.
11. Generate GC001 PB3 diagnostic payload.
12. Preserve evidence to Drive.
13. Classify PB3 explicitly before PB4.

## Hard boundaries

- no generative redraw
- no Golden/v12 production authority
- no area-only semantic deletion rule
- no observer/advisor score becomes a lone production action
- existing protect/keep/prune hard guards remain unchanged during initial PB3 backport
- deterministic production output remains byte/stage stable unless a later explicit promotion is separately approved

## Expected classification

**IMPLEMENTED + OBSERVER/ADVISOR-ONLY diagnostic expansion**

## After PB3

PB4 / SA4 Semantic Debug Board Backport.

PB4 will visualize why PB2/PB3 evidence was retained, merged, suggested for omission, or rejected while clearly separating observed evidence, advisor output, and production decisions.

## Current state declaration

The canonical continuation point is:

**PB4 / SA4 Semantic Debug Board Backport**
