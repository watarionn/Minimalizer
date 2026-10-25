# Lane A L02: signed H06 cuff-interior retention, exposed known-case hypothesis (2026-10-26)

**Research-only. No semantic owner promotion, renderer change, Golden approval, or production release.** L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.

## Goal and authenticated inputs

Avoid losing both large white sleeve cuffs in H06 while refusing to assign ambiguous cuff boundaries to skin or tan coat. Use **only** the signed original source RGB/alpha, frozen Run30 owner and class IDs, and existing source-only hue abstention to form the candidate. Human review masks were opened **only after the candidate was frozen** for scoring. H04/H06/H08 are exposed known characters, not an unseen blind set.

The four canonical non-shared Drive ZIPs match their existing SHA-256 pins: reviewed `6d7079b51c1d9e8c49e77af722252d2a466bcdfceb3e2851cf816265a3e17598`, Run30 `6ac735cc5105c860521b5d3dff567268a8b2a77d8195501d5046644b26ad1f5c`, sleeve observer `a4322f81a9b783bcad5dd21c2fe2ff5470af9399517f2aa88c9918345e3d7af7`, AnimeSeg `9a3f27edac23e14c219ff3a743c85321519cbe7c621c3f962d19e84ad6eb1e26`. Internal reviewed/Run30/AnimeSeg SHA manifests: **19/19, 7/7, 5/5**. Embedded original H06 WebP SHA `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` agrees with the signed review audit.

The existing hue-conflict → seed-contact → 4-connected topology repair source-only stages were independently reconstructed on the frozen Run30 H06 owner. The unapproved provisional mask reproduced its exact pinned SHA `df86e0ad3b018e1c25a996c2d9d1788f58865b41a496780a5408a2acbaff770e` (**10,484px, 2 components**). This is the **older frozen stage**, not a claim of re-running the later composed coat owner; the previous signed composed-frontier replay separately reported the same provisional mask SHA.

## New source-only boundary-core proposal

The A-only helper `propose_neutral_underlayer_boundary_core_shadow` runs the existing neutral-preservation candidate and **abstains from the 2px 8-neighbour outer boundary** of each provisional source island. It rejects any erosion that erases or splits an original island. It does not invent RGB, cross source alpha, change coat ownership, use human masks for inference, or assert underlayer semantics. The 2px radius is an **exposed known-H06 exploratory hypothesis**, not a trained, blind-validated threshold. It must not be retuned against the review labels and presented as unseen generalization.

| H06 signed postscore | Prior provisional | 2px interior proposal |
| --- | ---: | ---: |
| Original-source candidate pixels | 10,484 | **8,781** |
| Reviewed correct white underlayer | 10,177 | **8,730** |
| Known arm wrongly in candidate | 49 | **0** |
| Known coat wrongly in candidate | 8 | **0** |
| Unreviewed / unknown | 250 | **51** |
| 8-connected source islands | 2 | **2** |

The 1,703 abstained boundary pixels include **1,447 reviewed correct underlayer**. This loss is real and is not hidden. The core mask SHA-256 is `70315230fd5bb68de8dde8afd6b2a68ae4a04970258f6e7f6fd87b9c13c5b1b0`. Source alpha inclusion **8,781/8,781**, coat-owner overlap **0**, candidate component count **2→2**. The two white cuffs remain recognizable in a private source-pixel preview; no synthetic drawing or inpainting was used. The private masks/preview and coordinates are not published to GitHub.

## Decision and next integration gate

**Meaningful known-case provisional improvement:** 8,730 reviewed cuff pixels can be retained as separate source-backed material with **zero currently known arm/coat intrusion**. This is not an accepted P0 fix: **51 pixels are unknown**, boundary erosion loses genuine cuff edges, and the source-only core has **no independently validated semantic owner**. Accepted actual rendered-image P0 improvements **0**, P1 improvements **0**; H04/H06/H08 remain **3 unresolved P0 cases**. PR #436 stays **Draft / unmerged**.

A-only source-free helper and synthetic regressions were added. A local independent reconstruction of the signed H06 mask and two synthetic component-guard probes passed; **the exact updated GitHub-head pytest and repository-wide CI are not yet verified**. Next: run exact-head code with the latest composed owner, independently inspect visual cuff-edge continuity, test H04/H08 negative domain and a genuinely unseen signed character, then Phase4 owner exclusivity/connection/critical-parts PASS before Phase5. Do not auto-promote based on known-only postscore.

No changes to Lane B L04/L07, Public/C08, production LocalWorker, Golden, source originals, or private Drive artifacts.


## 2026-10-26: unowned class32 composed-promotion provenance guard

Source-free audit found that the composed-owner input contract previously allowed
**arbitrary unowned class32 pixels to become coat owner** as long as the
source alpha, class domain and 4/8 coat-component identity remained valid.
The existing hue-abstention resurrection check protects *previously owned*
class32 pixels, but not newly promoted class32 pixels. A 64x64 synthetic
counterexample keeps the coat's 4/8 component counts at 1/1, yet the old
predicate accepts the extra class32 pixel. This is a **potential large
skin/underlayer-to-coat P0 regression**, not an observed rendered fix.

The historical source-free signed H06 composed replay attributes its **3,162
existing owner promotions exclusively to class30**, not class32. Accordingly,
this H06-only research adapter now rejects any new composed-owner promotion
outside class30. A matched synthetic class30 control still passes. The
existing neutral cuff mask is not promoted, and the source-free 2px boundary
candidate remains unapproved. No reviewed labels or coordinates enter
inference. The synthetic counterexample and class30 control were checked
independently; **exact updated GitHub-head pytest, fresh signed H06 replay,
full CI and unseen-character blind remain NOT_RUN/PENDING**. The historical
H06 promotion breakdown is not a substitute for a fresh replay.

Accepted rendered P0/P1 improvements **0/0**; H04/H06/H08 **3 unresolved**.
PR remains Draft, Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD /
production NO_GO. No Lane B, Public/C08, production Worker or Golden change.
