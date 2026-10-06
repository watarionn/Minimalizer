# SA7.47 Layer / Occlusion Evidence Research — 2026-10-06

Status: CONTRACT PASS / GC001 SOURCE-EVIDENCE PASS / PRODUCTION NO-OP

SA7.47 absorbs LayerPeeler / SuperSVG layer reasoning as non-authoritative source evidence.

## Purpose

Describe pairwise semantic-role relationships without changing canonical anatomy, topology, z-order, or rendering authority.

Observed relationship classes:
- OVERLAP
- TOUCHING
- DISJOINT

Optional direction may be recorded only when an existing canonical z-order is explicitly supplied.

Overlap by itself never invents front/behind direction.

## New module

`minimalizer_zerobase/semantic_abstraction/layer_occlusion_evidence.py`

Contract version:
`sa7.47-v1`

### LayerRelationEvidence

Records:
- role A / role B
- relation
- overlap pixels
- overlap ratio relative to each role
- boundary contact pixels
- optional front role / back role
- direction source
- authoritative=false

### LayerOcclusionReport

Records:
- sorted role set
- deterministic pairwise relation graph
- whether canonical z-order was observed
- authoritative=false
- production_output_changed=false

## Direction boundary

Direction is not inferred from source overlap.

Without canonical z-order:
- overlap/contact direction = unavailable

With existing canonical z-order:
- higher observed z-order is reported as front
- lower observed z-order as back
- direction source = canonical_z_order_observation

Equal canonical z-order:
- explicit ambiguous state

Partial z-order:
- explicit partial state

Disjoint pair:
- direction not applicable

The observer never modifies z-order.

## Verification

Focused SA7.47:
- 9/9 PASS

Full ZeroBase:
- 678/678 PASS

Other:
- Python compileall: PASS
- git diff --check: PASS

Covered:
- overlap without invented direction
- observed canonical z-order direction
- touching vs overlap separation
- explicit disjoint relation
- equal-z ambiguity
- partial-z evidence
- mapping-order invariance
- mask shape mismatch fail-closed
- unknown z-order role fail-closed

## GC001 source-mask evidence

Roles:
- accessory_or_held_object
- hair
- head
- left_arm
- lower_body
- major_clothing
- right_arm
- torso

Pair count:
- 28

Relations:
- OVERLAP: 1
- TOUCHING: 13
- DISJOINT: 14

### Dominant overlap

hair <-> head

- overlap pixels: 12,421
- hair overlap ratio: 0.708112
- head overlap ratio: 0.720936
- boundary contact pixels: 13,408
- front role: unavailable
- back role: unavailable
- direction source: unavailable
- authoritative: false

Interpretation:
the source masks strongly support that hair and head occupy overlapping semantic space, but they do not by themselves authorize a front/behind decision.

This is the intended LayerPeeler-inspired separation:
- observe layered evidence
- do not confuse observation with render authority

## Production impact

- production image changed: false
- canonical z-order changed: false
- anatomy/topology authority changed: false
- Golden/v12 used as production input: false
- generative decomposition used: false

## Drive preservation

Folder:
`chatGPT及びCodex用/Minimalizer/Differentiable Minimalization Research/Golden_Comparison/GC001_IMG_1205/Semantic_Abstraction/SA7_47_20261006_LAYER_EVIDENCE`

Folder ID:
`1OpJX3w_nj9V8jdbDod7E8QPkgr2_fDPT`

Verified cloud artifacts:

- `GC001_sa747_layer_occlusion_evidence.json`
  - `1xCd-KjAR3uDQ_y54ds65bdxNBw80kZqp`
- `GC001_sa747_layer_context_4way.png`
  - `1TZP1AKjP1Uf_I5z-gSshen-Nr4OljjJe`

## Decision

Merge SA7.47 as observer-only infrastructure.

The contract is suitable for:
- PB2 / SA2 Evidence Adapter backport
- PB4 Semantic Debug Board
- PB6 Anatomy / Occlusion observer evidence

Do not change production z-order or visual baseline in SA7.47.

## Next

SA7 Closeout / Integration Gate.

Closeout must confirm SA7.42-SA7.47 work together under one canonical safety contract, then hand control to the adopted Post-SA7 Precedent Backport Pass beginning at PB2 / SA2 Evidence Adapter.
