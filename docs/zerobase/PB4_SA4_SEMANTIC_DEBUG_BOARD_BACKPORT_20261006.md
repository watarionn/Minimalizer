# PB4 / SA4 Semantic Debug Board Backport — 2026-10-06

Status: IMPLEMENTED + DIAGNOSTIC-ONLY

Primary precedents:
- CLIPasso / CLIPascene
- SuperSVG
- LayerPeeler

## Goal

Backport an inspectable semantic debug board into SA4 so PB2/PB3 evidence can be audited without changing production geometry, palette, z-order, importance, omission, or rendering.

PB4 separates:
1. observed evidence;
2. advisor evidence;
3. promoted production authority.

The machine-readable payload is canonical.
Text and PNG boards are deterministic views of the same payload.

## New module

`minimalizer_zerobase/semantic_abstraction/precedent_debug_board.py`

Contract version:
`pb4-v1`

New contracts:
- `PB4ComponentRow`
- `PB4SemanticDebugBoard`
- `build_pb4_semantic_debug_board(...)`
- `canonical_pb4_debug_json(...)`
- `render_pb4_debug_text(...)`
- `render_pb4_debug_image(...)`

The PB4 module is intentionally not re-exported from the semantic_abstraction package root.
This avoids introducing a circular dependency between the diagnostic board and PB3 importance diagnostics.

## Canonical board payload

Per component:
- component ID;
- role;
- support ratio;
- evidence authority state;
- removal observer availability;
- removal impact;
- merge observer availability;
- merge impact;
- merge target;
- primitive advisor status;
- primitive advisor agreement;
- PB3 recommendation;
- recommendation reasons;
- production action;
- hard-fail override allowed=false.

Global summaries:
- role component counts;
- relation counts;
- recommendation counts;
- observer availability counts;
- authority counts;
- advisor-context count;
- semantic-context score/status;
- hard failures;
- production policy changed=false;
- production output changed=false;
- adopted visual baseline.

## Authority visibility

The board exposes three explicit categories:

- OBSERVED EVIDENCE
- ADVISOR EVIDENCE
- PROMOTED PRODUCTION AUTHORITY

Authority provenance is read from PB2 Evidence.

Validation:
- observed/advisor evidence must declare production_authority=false;
- promoted evidence must explicitly declare production_authority=true;
- unknown authority states fail closed.

PB3 production actions are forbidden.
If any PB3 component row has a non-null production action, PB4 fails closed.

## Hard-failure visibility

Hard failures remain a dedicated list in the canonical board.

A perfect semantic-context score cannot hide or clear hard failures.

The text renderer prints each hard failure explicitly as:
`HARD FAIL: <reason>`

Board metadata always states:
- hard_failures_visible=true
- hard_fail_override_allowed=false

## Determinism

PB4 sorting is deterministic:
- PB2 components by evidence ID;
- PB2 relations by evidence ID;
- recommendation/role/relation summaries by key.

Input-order invariance is tested for:
- PB2 Evidence order;
- canonical JSON;
- plain-text rendering;
- PNG pixel output.

## Input and production immutability

PB4:
- does not mutate PB2 Evidence;
- does not mutate PB3 reports;
- does not call ImportanceEngine;
- does not call Phase 8 omission policy during board generation;
- does not alter production output.

Dedicated regression tests snapshot:
- PB2 Evidence serialization;
- PB3 report payload;
- ImportanceEngine result;
- Phase 8 omission result.

All remain unchanged after board generation.

## Verification

Focused PB2/PB3/PB4:
- **35/35 PASS**

Full ZeroBase:
- **713/713 PASS**

Other:
- Python compileall: **PASS**
- git diff --check: **PASS**

Covered:
- deterministic payload;
- mapping/input-order invariance;
- every PB3 component exactly once;
- recommendation reasons preserved;
- removal observer unavailable visible;
- merge observer unavailable visible;
- advisor unavailable visible;
- high semantic score cannot hide hard failure;
- observed/advisor/promoted authority explicit;
- production action must remain null;
- PB2/PB3 component mismatch fail-closed;
- PB2/PB3 input immutability;
- ImportanceEngine no-op;
- Phase 8 omission no-op;
- deterministic PNG output;
- invalid static layout fail-closed.

## GC001 real board

Components:
- **83**

Role counts:
- accessory_or_held_object: 2
- hair: 11
- head: 1
- left_arm: 16
- lower_body: 2
- major_clothing: 31
- right_arm: 1
- torso: 19

Relations:
- OVERLAP: 1
- TOUCHING: 13
- DISJOINT: 14

Recommendations:
- insufficient-evidence: **83**
- retain-evidence: 0
- merge-candidate-evidence: 0
- omission-candidate-evidence: 0

Observer availability:
- removal available: 0
- removal unavailable: 83
- merge available: 0
- merge unavailable: 83

Authority:
- observed Evidence: **111**
- advisor Evidence: 0
- promoted production authority: **0**
- advisor context rows: 0

Semantic context:
- status: AVAILABLE
- score: **0.7298672763136121**

Hard failures:
- 0 for this PB4 GC001 diagnostic context

Production state:
- production_policy_changed=false
- production_output_changed=false
- existing SA7.44 candidate SHA unchanged=true

Adopted visual baseline displayed explicitly:
`a60aaa12ff22c2f6384a598442964710ce939d87`

## Interpretation

PB4 makes the PB3 fail-safe state directly inspectable.

The board shows that:
- global semantic evidence exists;
- per-component semantic perturbation evidence does not;
- advisor evidence does not exist;
- production authority has not been promoted;
- all 83 components therefore remain insufficient-evidence;
- no prune/merge/retain production action was issued.

This is a successful safety state, not a processing failure.

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB4_SA4_20261006`

Folder ID:
`1ChMsJKXfY6kX0Pe2VV3v05JJ_QuDITn3`

Verified cloud artifacts:

- `GC001_pb4_semantic_debug_board.json`
  - `1rcErOWvaFv6z_SKR8cJMPCtGdbU9mCtT`
- `GC001_pb4_semantic_debug_board.txt`
  - `1tpva43O6yqTgOJmPGBq7vLYAOM93kTcb`
- `GC001_pb4_semantic_debug_board.png`
  - `1BL2Ew62I1AiroYq9_O_1kK3JvOzI4XD9`

## Classification

**IMPLEMENTED + DIAGNOSTIC-ONLY**

PB4 is complete.

## Next

PB5 / SA5 Face Neutralization Compatibility Audit.

PB5 must not replace or weaken the SA7.38 canonical face raster safety contract.

Goal:
prove that PB2/PB3/PB4 precedent-derived observer/debug infrastructure can coexist with face-neutralization safety while maintaining:
- Forbidden Face Detail = 0.00%;
- no face-feature promotion;
- no observer/advisor authority escalation;
- no production-output change from diagnostic layers alone.

PB5 may correctly end as NO-OP-BY-DESIGN if no safe face-layer implementation improvement is justified.
