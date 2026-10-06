# HND-20261006 Minimalizer PB2 / SA2 Evidence Adapter Backport

Date: 2026-10-06
Status: SA7 COMPLETE / PB2 NEXT
Repository: watarionn/Minimalizer
Canonical branch: main

## Canonical restart point

Restart from current `main`.

SA7 closeout:
`docs/zerobase/SA7_CLOSEOUT_INTEGRATION_GATE_20261006.md`

Cross-phase precedent plan:
`docs/zerobase/SA7_42_PRECEDENT_ASSIMILATION_PLAN_20261006.md`

## Why PB2 is next

The adopted execution order explicitly requires a bottom-up precedent backport pass after SA7.

Do not jump directly to SA8.

Order:
PB2 -> PB3 -> PB4 -> PB5 -> PB6 -> PB7 review -> SA8 -> SA9 -> SA10

## PB2 / SA2 Evidence Adapter Backport

Primary precedents:
- SuperSVG
- LayerPeeler
- LIVE

### Goal

Strengthen SA2 observation/evidence so later semantic decisions receive structured region/layer evidence rather than forcing SA7-era logic to rediscover it downstream.

Backport capabilities:
- explicit disconnected-component evidence
- region/layer candidate evidence
- source-supported adjacency / overlap evidence
- optional occlusion-direction provenance
- stable component/layer identities
- provenance separating observation from promoted authority

### Existing SA7 assets to reuse

From SA7.42:
- multi-component source region identity
- cluster/component separation

From SA7.44:
- residual component extraction and source-support telemetry

From SA7.47:
- OVERLAP / TOUCHING / DISJOINT relation evidence
- optional canonical-z observation with no authority transfer

PB2 should reuse these concepts at the evidence boundary rather than duplicate them.

### Authority contract

PB2 evidence is observer data by default.

It must not:
- directly choose production geometry
- alter anatomy/topology authority
- alter z-order merely from source overlap
- use Golden/v12 production information
- depend on generative decomposition
- hard-code GC001 structure

Every evidence record must preserve source/provenance.

### Required outcomes

PB2 must end with one explicit classification:
- IMPLEMENTED
- OBSERVER-ONLY
- NO-OP-BY-DESIGN

Expected classification:
**IMPLEMENTED + OBSERVER-ONLY evidence expansion**

### Preferred implementation order

1. Inventory current SA2 Evidence Adapter schemas and call sites.
2. Define the smallest backward-compatible region/layer evidence extension.
3. Reuse deterministic connected-component identity.
4. Bind layer-relation evidence without granting direction authority.
5. Add provenance fields that distinguish:
   - observed
   - advisor
   - promoted production authority
6. Add synthetic tests for:
   - disconnected components
   - overlap/contact/disjoint
   - mapping-order determinism
   - provenance
   - unavailable optional evidence
7. Verify no canonical rendering changes merely from enabling PB2 evidence.
8. Run full ZeroBase.
9. Evaluate GC001 evidence payload.
10. Preserve artifacts and classify PB2.

## Hard boundaries

- no generative redraw
- no Golden/v12 production authority
- existing Feature Survival / face / anatomy / topology gates remain hard
- observer evidence cannot silently become geometry authority
- deterministic production output must remain stable unless a later explicit phase promotes a rule

## Current state declaration

The canonical continuation point is:

**PB2 / SA2 Evidence Adapter Backport**
