# PB6 / SA6 Anatomy / Occlusion Evidence Backport — 2026-10-06

Status: **IMPLEMENTED + OBSERVER-ONLY DIAGNOSTIC / GC001 AUDIT PASS**

## Scope

PB6 adds a non-authoritative compatibility diagnostic between PB2 source-mask relations and the existing canonical semantic topology.

It does not replace or weaken `anatomy_integrity_gate`, create anatomy, rewrite topology, mutate z-order, or produce rendering actions.

## Implementation

- `minimalizer_zerobase/semantic_abstraction/anatomy_occlusion_diagnostic.py`
- `tests/zerobase/test_pb6_anatomy_occlusion_diagnostic.py`

The diagnostic reuses PB2 `observe_mask_relations` and reports:
- SUPPORTING
- NEUTRAL
- POTENTIAL_CONFLICT
- INSUFFICIENT_EVIDENCE

Every diagnostic relation remains:
- authority_state = observer
- production_authority = false
- production_action = null

Relation-aware compatibility is fail-closed:
- `attached_to` may be supported by TOUCHING or OVERLAP and conflicts with DISJOINT;
- `overlaps` requires actual OVERLAP;
- positional/depth constraints such as `above`, `left_of`, `right_of`, and `in_front_of` are not proven by source-mask contact alone.

## Verification

GitHub Actions PB6 validation run #6:
- focused PB6 + anatomy + PB2 + SA7.47: **36/36 PASS**
- full ZeroBase: **734/734 PASS**
- compileall: **PASS**

The first validation attempts exposed harness-only issues (wrong PB2 test path and missing scikit-image dependency). Both were corrected before the green run.

## GC001 canonical inputs

PB2 source evidence:
- Drive ID: `1Tvy-i7-kLhuh-Abg6drFP3CA8J5OBeTR`
- 8 roles
- 28 pairwise relations
- OVERLAP 1
- TOUCHING 13
- DISJOINT 14

Canonical semantic plan/topology:
- `GC001_semantic_debug_20261005.json`
- Drive ID: `15hVUZbiCikXRACZtfmux8uh8gYTHrvnU`

No Golden raster or Browser fallback v12 was used as production authority.

## GC001 PB6 result

Compatibility:
- SUPPORTING: **2**
- POTENTIAL_CONFLICT: **3**
- INSUFFICIENT_EVIDENCE: **1**
- NEUTRAL: **22**

Notable observations:
- hair <-> head: OVERLAP supports canonical `overlaps`;
- major_clothing <-> torso: TOUCHING supports canonical `attached_to`; source contact does not prove `in_front_of`;
- left_arm <-> torso: DISJOINT -> POTENTIAL_CONFLICT against required `attached_to`;
- right_arm <-> torso: DISJOINT -> POTENTIAL_CONFLICT against required `attached_to`;
- lower_body <-> torso: DISJOINT -> POTENTIAL_CONFLICT against required `attached_to`;
- head <-> torso: DISJOINT is INSUFFICIENT_EVIDENCE for canonical `above`, not an anatomy rewrite signal.

The three potential conflicts are diagnostics only. Existing canonical anatomy validation remains authoritative.

## Authority and production invariants

- production authority count: **0**
- production action count: **0**
- anatomy gate before diagnostic: **PASS**
- anatomy gate after diagnostic: **PASS**
- anatomy guard unchanged: **true**
- structural validation: **PASS**
- production candidate SHA before: `fcd47e67f2a78d5e0d635557b5bb58d1d77fb0478cfb05379b821b9dde6e034d`
- production candidate SHA after: same
- production candidate unchanged: **true**
- production output changed: **false**

## Drive preservation

Folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Post_SA7_Backport/PB6_SA6_20261006`

Folder ID:
`1wooOOpE5BJLXGIAB_CyYUFhW2YtS388U`

Verified artifact:
- `GC001_pb6_anatomy_occlusion_audit.json`
- Drive ID: `160PaSgAdAPNkTUbSKGJ2iCdE12GEgqVI`

## Classification

**IMPLEMENTED + OBSERVER-ONLY DIAGNOSTIC**

PB6 is complete.

## Next

PB7 / SA7 Precedent Integration Review.

PB7 should review PB2-PB6 together, remove duplication, confirm authority boundaries, and decide whether any evidence deserves an explicit deterministic promotion before SA8.
