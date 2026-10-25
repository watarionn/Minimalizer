# Lane A L02: signed H06/H08 residual taxonomy, 2026-10-25

**Research-only postscore. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** New accepted P0/P1 visual improvements: **0/0**. H04/H06/H08 remain unresolved.

## Authenticity and order

Re-read the canonical non-shared Drive originals, Run30 owner, SegFormer frozen class IDs and offline AnimeSeg classes. ZIP SHA-256 and reviewed/owner/AnimeSeg member manifests (19/7/5) were checked. Signed original RGBA SHA was checked against the reviewed trace before reconstructing owner maps. **Both source-only owner proposals were frozen before opening any human evaluation masks.** H06 composed owner SHA-256 `ceaae1199d673d07411bf120aca46f3415df69c0c5dee1395a2536d414b2602c`; H08 sequential composed→strict→single-anchor→contact-density class32→class30 opt-in owner SHA-256 `94122b855f70347ff6f318e02bbfa03cddd77e74e76c3772bfe59011df0b0086`.

The reproduced exposed postscore matched H06 TP **294,020**, known FP **1,077**, FN **20,803**, and H08 TP **144,221**, known FP **17**, FN **12,349**. Model weight bytes were not reauthenticated; H04 and a genuinely unseen signed character were not replayed. Unknown owner pixels remain unknown, not false positives.

## Previously unquantified P0 cause

| Signed case | Reviewed garment FN | FN in class32 | FN outside class32 | FN in class0/2/7 | Other notable missing class |
| --- | ---: | ---: | ---: | ---: | --- |
| H06 | 20,803 | **8** | **20,795** | 10,245 | class25 **9,913**; class30 637 |
| H08 | 12,349 | **4,073** | **8,276** | **6,330** | class30 1,892; class29 54 |

Even an impossible perfect recovery of **every** remaining class32 pixel leaves at least **20,795 H06** and **8,276 H08** reviewed garment pixels missing. Class32-only threshold/palette tweaking cannot finish the P0 repairs. This is a mathematical ceiling on an exposed reviewed-label score, **not a source-only owner promotion, blind generalization, or semantic PASS**.

**H06 annotation caveat:** 9,913 of its reviewed outerwear FN are frozen SegFormer **class25**, an accessory/bag category. The signed visual investigation in [PR #437](https://github.com/watarionn/Minimalizer/pull/437) already rejected **6,586** class25 pixels as visible patterned bag occluding the coat, despite the coarse reviewed outerwear polygon calling them positive. The 9,913 taxonomy count is a conflict, **not proof that all 9,913 are bag**. Do not change the signed human review, count them as recovered coat, or treat unknown as known negative. An authorized occlusion-aware boundary review is still needed.

**H08 remaining P0:** 6,330 reviewed garment-missing pixels lie in class0/2/7, plus 4,073 class32. No class0/2/7 OR promotion is authorized by this diagnostic. Independent garment-versus-arm/hair/accessory semantic evidence is needed. A source-only local-colour experiment found 967 additional H08 reviewed garment pixels **but also 3 new arm false-owner pixels**. A broader risky-class variant exposed 15,395 speculative H06 additions. **Both candidates were rejected; neither changes the accepted baseline.**

## Source-free code and next gates

The new `tools/research/local_l02_known_residual_taxonomy_postscore.py` is a **post-inference-only** diagnostic. It never creates pixels or changes owners. Negative tests verify alpha, class domain, unknown-aware FP, review inclusion, and the class32 optimistic bound. Original RGB/alpha, masks, NPZ, coordinates and private visual boards remain in the canonical non-shared Drive; only aggregates and source-free code are committed.

Next substantive target: independent H08 sleeve/arm/garment semantic separation and H06 bag-versus-coat occlusion review, then H04 P0 correction, complete Phase4 owner exclusivity/critical-part retention, unknown signed blind, full CI, Phase5 actual replay and user Golden/iPhone acceptance. B L04/L07, Public/C08, LocalWorker, Golden and production are unchanged.
