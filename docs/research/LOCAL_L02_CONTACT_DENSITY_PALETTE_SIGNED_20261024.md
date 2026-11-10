# Lane A L02: signed H08 contact-density + source-palette sleeve recovery (2026-10-24)

**Research-only, exposed known cases, Phase4 FAIL.** This code is not connected to production inference. It partially restores a visible portion of the H08 patterned sleeve, but does not certify garment semantics, unseen-character generalization, Golden, L03 or Local release.

## Signed real-image evidence

The four pinned non-shared Drive archives (ReviewedEvidence, SleeveSemanticIndependent, Run30 OwnerMasks, AnimeSeg Offline384) passed SHA-256 verification. Their reviewed/owner/AnimeSeg member manifests passed **19/7/5**. H04 additionally used the signed Run121 AnimeSeg observation. Original H04/H06/H08 embedded image bytes were checked against signed-review source SHA. H06/H08 baselines were independently reconstructed from signed original RGB/alpha and frozen SegFormer/AnimeSeg observations, then matched their pinned SHA before this proposal. All three source-only candidate arrays were frozen **before opening any human evaluation mask**. Two independent replays produced byte-identical source-free reports, SHA-256 `d2d4a7dc1f9571684f918ca77d8a01f9c2d27a72292223ba0f7f2a4884ca68ed`.

| Exposed signed case | Baseline TP / known FP / FN | Candidate TP / known FP / FN | New TP / known FP / unknown |
| --- | --- | --- | --- |
| H04 | 49,386 / 4,423 / 3,186 | unchanged | 0 / 0 / 0 |
| H06 | 294,020 / 1,077 / 20,803 | unchanged | 0 / 0 / 0 |
| **H08** | **137,789 / 0 / 18,781** | **143,372 / 17 / 13,198** | **+5,583 / +17 arm / +423 unknown** |

H08 known-only IoU: **0.880047 → 0.915606**. Source-only 4/8 frozen component identity and no-new-cross-owner-contact checks passed. The private visual comparison shows a fuller patterned sleeve. The **17 new arm false-owner pixels remain a semantic defect**; the 423 unreviewed pixels remain **unknown**, never positives or negatives. H08 still misses 13,198 reviewed outerwear pixels. H06's bag/coat occlusion disagreement and 1,077 underlayer FP remain. H04's 4,423 known FP remain.

**P0 cases partially improved: 1 (H08); P0 cases fully resolved: 0; P0 cases unresolved: 3 (H04/H06/H08); new P1 improvements: 0.** This known-case-explored candidate is NOT an independent blind validation or Phase4 quality PASS.

## Mechanism and safety

`local_l02_contact_density_partition_shadow.py` considers only unowned original-alpha SegFormer class32 components with >=1,024 pixels, >=10% owner contact and >=32 independent AnimeSeg generic-clothes observations. These structural parameters were explored on known cases, not blind validated. Nearest frozen **4-connected** owner-component assignment and 8-neighbour conflict deletion preserve both 4/8 component identities and existing owner pixels.

`local_l02_contact_density_palette_shadow.py` applies the previously established source-RGB LAB palette policy (8 clusters, 95th percentile, cap 25), trained only on frozen class32 owner pixels with independent generic-clothes support. It deletes detached additions, rejects new cross-owner contacts, and never creates source pixels, repaints existing owners, draws face features, uses human polygon coordinates, or imports reviewed labels for inference. Generic-clothes class is **not** proof of outerwear. No img2img, inpainting, or Golden replacement.

Isolated source-free candidate tree: **255 pytest PASS + 31 subtests**, including six targeted invariants. Full GitHub CI was **not run** when this report was written. Existing PR #429 remains separate, Draft and unmerged. The private owner NPZ and private visual comparisons are not committed here. The private candidate must remain in the existing non-shared Drive evidence hierarchy.

## Integration gate

The two new modules and targeted tests may be integrated **only as dormant research code**. They must not be wired into LocalWorker/production or used to claim semantic owner authority. Before Phase4/Phase5 promotion: independent signed unseen-character blind evaluation, arm/underlayer semantic repair (including H08's 17 new arm FP), H06 bag/coat occlusion review, whole-body/critical-part retention, full CI, then actual Phase5 source replay and user Golden/iPhone acceptance.

**L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No Lane B L04/L07, Public/C08, LocalWorker, Golden or release changes.
