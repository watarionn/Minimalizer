# PB2 / SA2 Evidence Adapter Backport — 2026-10-06

Status: IMPLEMENTED + OBSERVER-ONLY

Primary precedents:
- SuperSVG
- LayerPeeler
- LIVE

## Goal

Backport the structured region/layer evidence learned during SA7 into the original SA2 Evidence boundary without granting observation records semantic, geometry, topology, z-order, or rendering authority.

PB2 extends Phase 2 evidence production only.

It does not:
- perform EvidenceFusion;
- choose semantic truth;
- select production geometry;
- alter canonical z-order;
- render pixels;
- use Golden or Browser fallback v12 as production input;
- invoke generative decomposition.

## Architecture

New lower-layer module:

`minimalizer_zerobase/analyzers/structured_mask_evidence.py`

The module provides:

1. deterministic connected-component observation;
2. deterministic pairwise layer relation observation;
3. explicit evidence-authority provenance;
4. normalized observer-only `Evidence` records;
5. a PB2 expansion report with an explicit production-no-op flag.

SA7.47 was refactored to consume this lower-layer relation observer rather than maintaining a separate copy of the same logic.

This fixes the dependency direction:

SA2 structured observation
-> later semantic abstraction observers
-> later policy / production decisions

rather than:

SA7-specific observation
-> imported backwards into SA2.

## Component evidence

Each non-empty semantic role mask is split into deterministic connected components.

Stable order:
- role ascending;
- component area descending;
- y;
- x;
- width;
- height.

Each component receives a stable ID:

`pb2:<role>:component:<index>`

Recorded fields:
- component bbox
- centroid
- pixel count
- parent role pixel count
- support ratio
- stable component index
- source reference
- authority provenance

The geometry field deliberately uses:

`component_bbox`

rather than the production `bbox` key.

Reason:
PB2 evidence must fail closed if accidentally sent into existing `EvidenceFusion`. It must never silently become a production region merely because it is structurally compatible with an old call site.

## Layer relation evidence

Every sorted role pair receives one relation record:

- OVERLAP
- TOUCHING
- DISJOINT

Recorded fields:
- roles
- overlap pixels
- overlap ratio relative to each role
- boundary contact pixels
- optional front role
- optional back role
- direction provenance

Direction contract:
- overlap alone never creates front/behind direction;
- without z-order evidence: `unavailable`;
- disjoint: `not_applicable`;
- partial z-order: explicit partial state;
- equal z-order: explicit ambiguous state;
- supplied existing canonical z-order may be observed as `canonical_z_order_observation`;
- PB2 never modifies z-order.

## Evidence authority provenance

PB2 defines three explicit provenance states:

- `observed`
- `advisor`
- `promoted`

These states are representational provenance, not automatic authority transitions.

PB2-generated records are always:

- state = observed
- evidence_scope = observer_only
- production_authority = false

Advisor state requires an advisor source.
Promoted state requires an explicit `promoted_by` provenance record.

Observed evidence rejects advisor/promotion provenance.
Invalid transitions fail closed.

No PB2 API promotes generated observer evidence.

## Production no-op boundary

PB2 observer records intentionally cannot be consumed silently by current `EvidenceFusion`.

If they are accidentally passed to `EvidenceFusion`, fusion fails closed because PB2 component/layer evidence does not expose the production `geometry.bbox` contract.

Synthetic production-no-op verification also confirms:

- existing SLIC Evidence bytes are unchanged;
- existing EvidenceFusion output is identical before/after PB2 evidence generation;
- PB2 expansion reports `production_output_changed=false`.

## SA7.47 compatibility

SA7.47 `observe_layer_occlusion` now consumes the generic SA2 relation observer.

Existing SA7.47 public report behavior remains intact.

Focused regression includes the full SA7.47 contract.

## Verification

Focused PB2 / Phase2 / SA7.47:
- **29/29 PASS**

Full ZeroBase:
- **689/689 PASS**

Other:
- Python compileall: **PASS**
- git diff --check: **PASS**

Covered:
- disconnected-component stable identity
- overlap / touching / disjoint
- no invented occlusion direction
- optional canonical z-order observation
- mapping-order determinism
- source provenance
- observed/advisor/promoted provenance distinction
- invalid authority transition fail-closed
- accidental EvidenceFusion fail-closed
- production Evidence immutability
- coordinate-space fail-closed
- SA7.47 compatibility

## GC001 evidence

Input:
canonical Phase 4 source part masks.

Roles observed:
- accessory_or_held_object
- hair
- head
- left_arm
- lower_body
- major_clothing
- right_arm
- torso

Role count:
- 8

Structured component count:
- **83**

Component counts:
- accessory_or_held_object: 2
- hair: 11
- head: 1
- left_arm: 16
- lower_body: 2
- major_clothing: 31
- right_arm: 1
- torso: 19

Layer relation count:
- **28**

Relation counts:
- OVERLAP: 1
- TOUCHING: 13
- DISJOINT: 14

Total PB2 observer Evidence:
- **111**

Authority-state count:
- observed: 111
- advisor: 0
- promoted: 0

Production authority count:
- 0

The relation distribution exactly preserves the SA7.47 GC001 observation:
- one source overlap;
- thirteen touching pairs;
- fourteen disjoint pairs.

## Production candidate integrity

Existing SA7.44 GC001 candidate SHA-256 was measured before and after PB2 evidence generation.

Result:
- unchanged: **true**

PB2 produced no new production image and modified no production candidate bytes.

## Interpretation

The component evidence makes the earlier architectural problem visible at the correct layer.

Examples:
- major_clothing: 31 disconnected components
- torso: 19
- left_arm: 16
- hair: 11

This does not mean production should render all 83 components.

It means SA2 can now report the actual source-supported component structure before SA3 and later stages decide:
- what matters;
- what can merge;
- what can be removed;
- what deserves geometry budget.

That responsibility moves to PB3 / SA3 rather than being hidden inside SA7 geometry logic.

## Drive preservation

Folder:

`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB2_SA2_20261006`

Folder ID:
`1TByZuKDRECM0CngUrN58vF3n8UAHHQ0I`

Verified cloud artifacts:

- `GC001_pb2_structured_evidence.json`
  - `1Tvy-i7-kLhuh-Abg6drFP3CA8J5OBeTR`
- `GC001_pb2_component_layer_board.png`
  - `1uQbM47a0AWP0F0fdIweiKyaO-3DKVrSi`

## Classification

**IMPLEMENTED + OBSERVER-ONLY evidence expansion**

PB2 is complete.

## Next

PB3 / SA3 Importance & Policy Backport.

Primary precedents:
- CLIPasso
- CLIPascene
- StarVector advisor

Goal:
use PB2 structured components together with SA7.45 semantic-retention evidence and SA7.46 primitive advice to measure removal/merge impact and semantic contribution without allowing observer/advisor scores to become lone production authority.
