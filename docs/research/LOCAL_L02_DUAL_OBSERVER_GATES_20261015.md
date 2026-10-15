# MinimalizerLocal L02, continuation: dual-observer garment evidence and independent-character gates

**Date:** 2026-10-15 JST. **Result:** H04 within-source quality improves; machine checks PASS. **Formal L02: HOLD / LocalWorker production: NO-GO.**

## Evidence and version identity

- Source: immutable H04 PNG SHA-256 `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` (Run105 signed source18 bundle).
- Human reference: `H04_FULLBODY_MANUAL_REFERENCE_V1` (17 user-drawn polygons). Three jacket polygons are authenticated by overlap with the previous user jacket-only trace. This is **human evidence for H04 only**, not an unseen-character ground truth.
- Primary observer: H04-manual-supervised HistGradientBoosting model using *spatially out-of-fold* H04 predictions, source-native RGBA/Lab/edge/position features, previous research PR #402. H04 hyperparameters were tuned using H04; not independent cross-character evaluation.
- Secondary observer: offline-CPU pretrained AnimeSeg `suzukimain/AnimeSeg` Mask2Former v3, checkpoint SHA-256 `f6764a379496712a92d1a85f852a81155cd79132a3e050b77c972be7e1cec394`, Run121 source-bound H04 result, original source SHA match. Reused **previously performed actual inference**, no new model output invented. Secondary `class_id=10` means **generic clothes**, not jacket-specific semantic ownership; confidence was uncalibrated.
- Secondary original-source `class_ids.png` member SHA `18190ac3d86c1376b319f0b1b17a89eb69a6b89e97ced3f935c03f09299965fb`, verified from private portable Run121 archive, SHA `bfcd6166820b5ac290460269a99af6e8ee5fb312bfc95f51980909e52a69a73c`.
- Phase5 graph **exact Git blob** `60848322332ac88297ef2688d06e32f17ed2b8bc`, reverified against the actual PC code before replay.

## Genuine H04 signed-source-aligned jacket diagnostics

Metrics compare original-source-coordinate, visible manual jacket shapes 3/9/10 to candidate masks in signed opaque pixels excluding protected parts. They are **not** Golden evaluations.

| Method | Jacket IoU | Precision | Recall |
|---|---:|---:|---:|
| Old source-color shadow | 0.607232 | 0.691453 | 0.832926 |
| H04 spatial OOF supervised learner | 0.799184 | 0.845551 | 0.935791 |
| AnimeSeg generic clothes ID10 alone | 0.768412 | 0.803588 | 0.946104 |
| Two-observer AND with 3-pixel class-boundary allowance, signed-owner-union clipped | **0.863355** | **0.935073** | **0.918411** |

- The first exploratory two-observer mask included **41 source-opaque pixels outside the original Phase4 owner foreground union**. Reprojecting to the signed owner union was mandatory. **Only the clipped 0.863355 metric is authoritative**; preliminary 0.863890 is superseded.
- After strict clipping, the evidence mask holds **51,427 source-owned pixels**; 18,209 source-owned pixels show inter-observer disagreement. Class-boundary allowance of 3px is a research setting checked only against H04, **not a calibrated universal rule**.
- Naively OR-ing evidence into original `major_clothing` caused its number of connected components to jump from **5 to 29**. **Rejected.** Do not regard high IoU as an acceptable Phase4 ownership edit.
- Instead the versioned private NPZ stores every `owner__PART` byte-preserved as inherited from the preceding *unapproved* Run188-derived v2 shadow, and a separate `observation__jacket` and `observation__disagreement`. Head/hair/torso/major-clothing components stay **1/4/2/5**. Foreground union XOR 0 relative to the inherited shadow (earlier work separately checked its union against the signed original); protected part owner changes 0. **The inherited owner map itself is not promoted as the immutable signed Phase4 truth.**
- Actual PC replay of **unchanged owner-only Phase5 input**, pinned blob above: **21 anchors, 13 relations, no isolated major part, no missing arm/core attachment, no occlusion cycle; PASS**. This is **not** a validation of a corrected exclusive clothing-owner map. The soft evidence is deliberately excluded from the graph and production renderer.
- Two independent H04 executions produced byte-identical output PNG, metrics JSON and NPZ SHA; independent reviewer signoff not fabricated.

## Failed scale normalization and unseen-source evaluation

Research tried exact original foreground alpha-bounding crop normalized to 900px, 1100px, and 1200px analysis height. Resampling is for ephemeral analysis only; it does not create signed source pixels or replace original owner masks. Safety checks reject opaque backgrounds and reprojected transparent pixels.

| H04 within-source spatial crossvalidation | IoU |
|---|---:|
| Previous native-image learner | **0.799184** |
| 900px normalized | 0.688735 |
| 1100px normalized | 0.723137 |
| 1200px normalized | 0.651572 |

**Normalization experiment failed the H04 no-regression gate** and is not adopted as new L02 inference. Diagnostic probe of other 17 signed Run105 inputs had 14 raw observations and 3 `ABSTAIN` (opaque backdrop), consistent with prior PR #403. H06, H08 and H17 900px outputs changed under resampling to 700px and 1100px (native IoU around 0.73–0.80); this shows input-scale instability, **not** semantic performance.

Only **one** of the source18 images, H04, has authenticated human jacket pixels. For H06 long coat, H08 pink outerwear and H03 skirt/negative control, no authoritative semantic jacket/arm references yet exist. **Precision/recall/IoU on separate characters must remain null.**

## Reproducibility and human intake

- Independent offline AnimeSeg inference for H06/H08 **NOT executed**: on actual PC memory-preflight available RAM was **3.32 GiB** (earlier 4.49 GiB, declining). To protect existing work and avoid stopping unrelated processes, CPU Mask2Former was not loaded. A 512/768-size run may only restart with adequate measured free RAM and a per-run admission gate; never claim a second-model result for H06/H08 without performing it.
- Two source-hash-pinned **empty** ReferenceShapeEditor v1.1 JSON projects for H06 and H08 were built and syntax/underlay verified, intended for private user review. They contain untouched original image data and **no drawn polygons**. They do NOT count as manual labels.
- Reusable fail-closed `verify_local_l02_manual_intake.py` validates original source SHA vs embedded image, full canvas, vertex/polygon integrity and semantic `outerwear/`, `arm_skin/`, `hair/`, `underlayer/`, `accessory/`, `unknown/` prefixes, then reconstructs *visible* masks respecting layer occlusion without inventing new source pixels. A project becomes review-ready only **after actual independent human drawings** are submitted and validated; not Golden approved automatically.
- New synthetic tests **55/55 PASS**, covering signed-source shape/extent, foreground, authenticity, independent observer identity, fail-closed quality gates, occlusion order and unsigned release refusal. Full H04 real rerun repeated byte-identically.

## Exact remaining L02 release blockers

1. H06/H08 real signed-source independent human outerwear and arm occlusion references (optionally a H03 no-jacket negative control). Use the prepared private editor starters. Until then H04 is the only labeled character.
2. Resource-admitted separate AnimeSeg inference H06/H08 (or another independent credible observer), authenticated model checkpoint, original source hashes and preserved review masks. Independently verify any new output bytes from private Drive.
3. Truly **out-of-character** evaluation: H04 train only, H06/H08 signed ground truths for jacket/arm visible boundaries and negative/positive errors. Set acceptance thresholds **before** selecting a new model; do not tune them from test labels.
4. Solve exclusive semantic ownership plus arm/sleeve/hair occlusion and Phase4→5 candidate replay. Soft evidence alone must never overwrite hair or clothing.
5. Only then reconsider L02 completion. Subsequent Stage8 ring budget, C04 Golden human A/B and owner iPhone signoff are separate later gates.

**Unchanged:** local production Worker and its graph, Public and PWA routes, scheduled C08 campaign, source originals and Stage4 signed masks. No generative fill, no face components, no new reference polygons in this research.
