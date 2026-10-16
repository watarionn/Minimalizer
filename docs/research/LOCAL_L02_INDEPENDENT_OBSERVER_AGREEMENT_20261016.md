# Local L02: two-independent-model jacket agreement and anatomical boundary evidence

**2026-10-16, research work package complete; garment-owner authority FAIL; L02 HOLD, Golden HOLD, production NO_GO.**

## Permission and evidence boundaries

The user explicitly reported on 2026-10-16 that the **SegFormer-B2 Fashion permission conditions have been resolved**. Record this as a user-provided clearance statement for subsequent evaluation. This research comparison does not independently inspect the terms of that permission or claim that model licensing alone approves product release. Historical noncommercial-research-only model report (#413/#414) is preserved as the state at that time, not retroactively rewritten.

Compare two previously pinned, independently pretrained observers:
- `sayeed99/segformer-b2-fashion`: jacket/coat native class predictions, weight SHA `47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1` (PR #413).
- `HasanKabir23/Yolov26s-DeepFashion2`: short/long-sleeve outwear instance predictions, ONNX SHA `485bc106721febbd82fe24297e12a9fb49a435a552afff1e6b76308716555f76` (PR #411).

A **pure source-mask partition** splits independent predictions into `shared`, `SegFormer-only`, `DeepFashion-only` and `neither`. Human manual annotation is used **only after** prediction for separate known-positive/known-negative/unknown diagnostics. No user polygon, mask, score threshold fitted on these three cases, or new source pixel enters inference or shadow owner transfer. `shared` is not granted semantic-owner authority.

## Actual three-character results

| Signed original | Shared outerwear pixels | Disagreement pixels | Shared labelled-only jacket IoU | Semantic decision |
|---|---:|---:|---:|---|
| H04 | **0** | 38,461 | **0.000000** | ABSTAIN: other observer detects no outwear |
| H06 | 189,054 | 159,308 | **0.592101** | SHADOW ONLY |
| H08 | 78,726 | 51,357 | **0.496398** | SHADOW ONLY |

H04 SegFormer-only region contains 34,581 labelled outerwear positives but misses sleeves and shoulder parts on visual inspection. DeepFashion2 predicts zero outerwear, so strict dual-observer intersection is empty. H06 shared region covers 186,407 human-labelled jacket pixels, with **128,416** labelled jacket pixels missing; it excludes explicit nonjacket negatives but misses much of the sleeves/hem. SegFormer-only H06 covers 147,738px, of which 74,131px are unlabelled source: **unknown, not confirmed jacket**. H08 shared region covers 77,721 labelled positives, leaving **78,849** labelled positives missed. H08 DeepFashion2-only predicted region contains **3,297 explicitly labelled arm pixels**; they are absent from the shared region, confirming its false-positive suppression but not a full semantic solution.

User-supplied, SHA-verified H04/H06/H08 original bytes and human visible masks were evaluated at their native source frame. The real validation image contacts were privately generated and **visually examined**: H04 jacket front captured while sleeves/shoulder missing, H06 model agreement favors interior coat and misses substantial sleeves/hem, H08 misses sleeve areas while DeepFashion2-only leaks into forearm/glove. Face features present in signed source are not a directive to draw them; intended Minimalizer output remains no eyes, brows, nose or mouth. These are *private diagnostic screenshots*, not user-accepted Golden.

All derived arrays are source-alpha clipped, mutually exclusive, and reconstruct original source alpha exactly. (2) independently executed replays gave identical source-free diagnostic JSON SHA `c0c92e20b876fa624e0969841560c87c90eb1b2f2219edc37b203dc2eb6df80e` and 3/3 predicted native masks identical (ZIP container timestamps differ, so do **not** claim byte-identical ZIPs). The new 15 synthetic authorization/unknown/tamper/shape/overwrite checks **all passed** on the local CPU. Full repository-wide CI was not run.

## Private Drive evidence now cloud-confirmed

These files are under the established `chatGPT及びCodex用/Minimalizer` folder and were **downloaded back through the Google Drive connector** and checked in an independent container:

- [Private signed consensus ZIP](https://drive.google.com/file/d/11tcbty2tfZJayG1tn_TaEW6siDhJLkyN/view), SHA-256 `f33c7b5238bce049e2ce676481c6962389b4a9a26deffc7ad988761bfa4e0a58`; contains full metrics JSON and per-case source-bound masks, no public export.
- [Private visual contact sheets](https://drive.google.com/file/d/1IF_9GAlXCQP_5N1Ba0e6_FFkwetv6Ta7/view), SHA-256 `1abcf46cb8b7885e489a9dca931fb7465452209ff8c29a7110ee637b9139362b`; full original pixels and human review are contained **only here**.
- [Prior SegFormer prediction ZIP](https://drive.google.com/file/d/1IYqsukUHmpdnWgmIwoZt_HEp6Vle7sk4/view) and [prior DeepFashion2 prediction ZIP](https://drive.google.com/file/d/1II9CbB6Fu0Br7d2bAWp2BaWQLiTy4xtW/view) now also cloud-readable. Previously recorded cloud-sync pending flags in earlier dated reports are **resolved as of this record** for these exact files.

The public [metrics JSON](LOCAL_L02_INDEPENDENT_OBSERVER_AGREEMENT_20261016.json), script `tools/research/local_l02_observer_consensus_shadow.py` and 15 pure synthetic tests contain no private source, polygons, or masks. LocalWorker, Public/C08, scheduled campaign, canonical Phase4 masks, and signed source pixels are unchanged.

## Gate disposition and next actionable work

**No auto-promotion.** In particular, forcing strict two-model agreement discards all H04 outwear and large H06/H08 regions. Union promotes an H08 arm false positive and extensive H06 unknown pixels. Neither method is approved for the source-owned exclusive jacket owner mask. Pinned Phase4→5 execution **not run for this candidate**, because the first-bad-stage is independent Phase4 meaning/occlusion evidence; do not represent an earlier H04-only graph PASS as new transfer validation. Continue with source-only confidence/occlusion-aware outerwear/arm boundary review, or an independent sleeve-aware model and fresh character holdouts, without using human reference masks in prediction. L03 follows only after the semantic visual gate passes, then Stage8 source vertex/expanded SVG/Chrome DPR1-DPR2 and actual user Golden/iPhone acceptance. Until then L02/Golden HOLD, release NO_GO, no Public or Local Worker production change.
