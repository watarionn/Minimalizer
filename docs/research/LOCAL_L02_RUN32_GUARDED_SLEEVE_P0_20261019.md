# Local L02 Run32: signed H08 sleeve P0 improvement, research HOLD

This is **source-only research**, not production promotion. Frozen signed H06/H08 original source SHA, SegFormer class5/10/32 predictions, independent AnimeSeg generic-clothes prediction and Run30 owner/candidate were reverified. Human annotations were used only after proposal for postscore.

A class32 pixel may be restored only if it is in the frozen source-alpha/candidate, has independent generic-clothes support, and is reachable from an existing jacket/coat seed by a 4/8-connected path entirely within those supported sleeve pixels. Nearest geodesic seed wins; ties and disconnected fragments abstain. Frozen owner pixels never change.

| Known case | Before labelled-only IoU | After | Correct sleeve pixels restored | Added known arm FP | Unscored added unknown | Remaining reviewed outerwear missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| H04 | not run (independent class map unavailable) | not run | 0 | not measured | not measured | not measured |
| H06 | 0.891885 | 0.891885 | 0 | 0 | 0 | 23,735 |
| H08 4-neighbour | 0.616561 | **0.753305** | **21,410** | **0** | 93 | **38,625** |
| H08 8-neighbour | 0.616561 | 0.752909 | 21,348 | 0 | 93 | 38,687 |

H08 source-masked visual comparison shows a substantial missing patterned sleeve region restored in the isolated outerwear shadow. The rest of the body/garment remains incomplete. H06 retains **11,326 underlayer** and **225 arm** known FP. H04 retains previously observed **4,423 known FP**. The generic AnimeSeg clothes class is not an outerwear ground truth, unknown pixels are not negative, and all H01-H18 were previously inspected. No independent unseen generalization.

Independent SciPy sparse-graph Dijkstra oracle exactly matched H06/H08 4/8 candidate owner arrays (0 differing pixels). H08 4-neighbour owner SHA-256: 823396225cd95e6cac8f12455e83ddc2f62d65ebc3ddbd25bba621edfe4b547c. H08 8-neighbour: d3cc3b75ab87c3a6ef8e2840450fec214eb5820efc3bd0288f57a419ef46697c. H08 jacket connected components 29→14 (4), 22→9 (8), coat component count unchanged. Source pixels generated 0; original owner XOR 0. 764 source-free synthetic/regression tests passed in the development sandbox.

Private original-masked RGB previews, owner NPZ and signed evidence must remain under Drive chatGPT及びCodex用/Minimalizer; do not commit them. No model-weight reauthentication this run, no full Phase4 owner/Phase5 replay, no new character or human Golden approval. **L02 HOLD / Golden HOLD / L03 NO_GO / Local production NO_GO**. B L04/L07, Worker, Public/C08 and release flags untouched.

Next P0: H04 arm/underlayer FP, H06 underlayer/arm FP, H08 remaining 38,625 missing reviewed outerwear, whole-owner Phase4 topology/arm/hair/neck preservation and independent unseen signed cohort.
