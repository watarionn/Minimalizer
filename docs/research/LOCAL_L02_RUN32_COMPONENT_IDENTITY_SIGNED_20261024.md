# L02 Run32 same-owner component identity repair, signed H06/H08 replay (2026-10-24)

**Research only. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** New resolved real-image P0/P1 cases: **0 / 0**. H04/H06/H08 remain unresolved.

## Failure found in merged PR #423

The Run32 contact-safe wrapper preserved frozen owner pixels and prevented **cross-owner** jacket/coat contact, but did not prevent **same-owner** merges of previously disconnected jacket components. On authenticated H08 Run30 inputs, the unmodified merged wrapper changed jacket component counts **29→14 (4-neighbour), 22→9 (8-neighbour)** while reporting contact safety. That is a P0 topology regression; it cannot be promoted to Phase4.

## Fix and source-only gates

The new `local_l02_frozen_component_gate.py` conservatively removes *new* pixels at collisions between immutable frozen components, then removes orphan additions and checks 4/8-neighbour component identity bijection. It never erases/reassigns a frozen owner and never reads human annotations. The Run32 contact wrapper invokes this after the cross-owner contact prune and before returning its source-only owner. Existing contact/alpha/class checks remain. Human labels are opened only after both candidate owners are frozen.

## Signed real replay, not an unseen blind test

All four existing private archive SHA-256 pins and embedded manifests were checked against the original private Drive files. Current GitHub main source blobs for the three merged safety modules were matched byte-for-byte before the test; only the new component guard and wrapper integration were changed locally. Signed H06/H08 RGB/alpha and independent SegFormer/AnimeSeg observations were used, with no human labels, annotation coordinates or inferred negative unknown pixels in the proposal.

| Case | Candidate | Known outerwear TP | Known FN | Known FP | Arm FP | Underlayer FP | Jacket components 4/8 | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| H06 | Run30 | 291,088 | 23,735 | 11,551 | 225 | 11,326 | 0/0 | Known P0 FAIL |
| H06 | new component-safe Run32 | 291,088 | 23,735 | 11,551 | 225 | 11,326 | 0/0 | No quality gain |
| H08 | Run30 | 96,535 | 60,035 | 0 | 0 | 0 | 29/22 | Known P0 FAIL |
| H08 | merged PR #423 contact-only | 117,801 | 38,769 | 0 | 0 | 0 | **14/9** | **Topology FAIL** |
| H08 | new component-safe Run32 | 116,566 | 40,004 | 0 | 0 | 0 | **29/22** | Topology preserved, quality still FAIL |
| H08 | prior best signed single-anchor | **137,789** | **18,781** | 0 | 0 | 0 | **29/22** | Existing known frontier, P0 still unresolved |

The new gate pruned 1,254 additional H08 proposed pixels after contact pruning (1,398 total vs unguarded Run32). **Every pixel of the new component-safe H08 Run32 candidate is already present in the prior best signed H08 owner**: 0 additional owner pixels beyond that best frontier. Therefore the component guard repairs a structural safety bug but **does not constitute a new visible P0/P1 improvement**. The H06 Run32 proposal adds 0 pixels; H06's underlayer/arm false owners remain. H04 was not freshly replayed here; its last known FP 4,423px remains pending.

## Reproduction and boundaries

Source-only negative tests include same-owner 4- and 8-neighbour merges, frozen-owner erasure/reassignment, and the Run32 wrapper. The private replay used the authenticated existing four archives, without exporting private bytes, masks, coordinates, model predictions, or visual boards. Private archive contents and all temporary private copies are not included in the public patch. The new gate requires only `numpy`, `scipy` and existing Lane A modules. It does not alter B L04/L07, Public/C08, LocalWorker, Golden, release or production.

Next priority remains H06 underlayer-vs-outerwear and H08 sleeve-vs-arm independent semantic ownership, not threshold tuning or counting additional test runs. Unseen signed character evaluation is **PENDING**. Phase4 semantic exclusivity/critical part preservation must PASS before Phase5 and Golden review.
