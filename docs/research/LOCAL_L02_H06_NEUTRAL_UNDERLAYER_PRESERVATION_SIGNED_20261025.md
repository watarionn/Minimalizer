# Lane A L02: preserve H06 source-neutral underlayer as a separate shadow (2026-10-25)

**Status: research-only Draft candidate. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No change to production inference, LocalWorker, Lane B, Public/C08, Golden or human approval. The H04/H06/H08 corpus is exposed; this is **not** unseen generalization.

## P0 mechanism and visible comparison

The integrated H06 class32 hue-abstention removes most wrong coat ownership but leaves removed original-source pixels unowned. The source-only `neutral-underlayer-preservation-shadow` preserves coherent, achromatic removed class32 pixels as a **separate, unapproved provisional layer**, while keeping the coat owner and 4/8 connectivity from the existing hue stage. It uses the existing fixed neutral hue condition (`saturation < 0.15`, `value > 0.50`) and existing 8-connected component floor (1,024px), not a new per-character postscore threshold. The source-only proposal has no human annotations, coordinates, polygon geometry, generation, inpainting or alpha expansion. It deliberately refuses mixed jacket/coat-owner cases such as H08.

Four canonical non-shared Drive ZIP archives were independently verified against the existing SHA-256 pins. Internal reviewed/Run30/AnimeSeg manifests verified 19/7/5 members. The embedded signed H06 source SHA matches `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`. Two source-only frozen replays and their postscore receipts are byte-identical (source-free report SHA-256 `d1750251344cbcab0c616545687e5c7ad207334037ec92ae2321b10285c94c3b`). No private RGB, NPZ, masks, coordinates or comparison image are committed.

| Signed H06 known review | Run30 frozen coat | Existing hue-abstained coat | Separate provisional layer |
| --- | ---: | ---: | ---: |
| Correct coat TP | 291,088 | 291,080 | not a coat owner |
| Missing coat FN | 23,735 | 23,743 | not a coat owner |
| Known coat false-owner FP | 11,551 | 1,077 | not a coat owner |
| Wrong underlayer in coat | 11,326 | 1,077 | not a coat owner |
| Correct reviewed underlayer retained separately | not represented | not represented | **10,177px** |
| Wrong arm / coat in provisional layer | n/a | n/a | **49 arm + 8 coat** |
| Unreviewed provisional pixels | n/a | n/a | **250 unknown** |

The source-only provisional layer has **10,484 source pixels across two components**. Private visual comparison shows original sleeve-cuff material retained separately from the tan coat rather than assigned to the coat. However, the 49 arm and 8 coat pixels are real semantic errors, and the 250 unreviewed pixels remain unknown. The provisional layer is **not an accepted semantic owner** and must not be rendered as underlayer without further independent evidence.

**Important frontier distinction:** this replay starts from the authenticated Run30 owner and the existing hue-abstention code. It does **not** reconstruct the later composed H06 frontier of **294,020 coat TP / 1,077 known FP / 20,803 FN**. Do not present the Run30-to-hue improvement or this separate provisional layer as a new accepted H06 coat-quality improvement. New accepted P0/P1 improvements: **0 / 0**; one substantial **provisional** H06 underlayer-retention candidate, zero resolved P0 cases, all H04/H06/H08 unresolved.

## Integration gates

This proposal may be staged only as dormant A research code. Before promotion: independently replay against the latest composed H06 owner, eliminate or explicitly reject arm/coat intrusion without sacrificing large correct underlayer regions, prove source-only Phase4 exclusive owner/connection/critical-part retention, run full CI and genuinely unseen signed blind, then Phase5 exact replay and user Golden/iPhone acceptance. Do not tune from the known H06 review labels. The generic-clothes observer is not specialized underlayer authority. No new model license or production permission is inferred.
