# Local L02: reviewed H04 + independent H06/H08 references, 2026-10-16

## Grounded user review and authority

The user submitted H04 (17 polygons), H06 (7 polygons), and H08 (4 polygons) ReferenceShapeEditor v1.1 JSONs, plus H06/H08 SVGs. Each embedded RGBA/WebP original matches its *previously signed* H04/H06/H08 source SHA-256 exactly. JSON and SVG polygons/names/vertices match for H06 **7/7** and H08 **4/4**. All masks are rasterized in source coordinates, original source-alpha-clipped, and last-visible-polygon-first for occlusion. No generated image pixels or filled missing areas.

The user explicitly clarified **right/left names are the subject's anatomical right/left**, never mirrored to viewer right/left. The user's H04 review accepted the four harmless, unintended >1.5%-outside-alpha overshoots (`sj`, `s1i`, `s1m`, `s4p`) with **no geometry changes**. The validator supports a *single pinned exception* only when BOTH exact H04 signed source SHA and canonical full-user-trace SHA match; no arbitrary input or other case is allowed to waive the strict 1.5% rule. The strict audit remains red; a separate `effective_geometry_review_pass` records this specific human acceptance. The submitted right/left names and original polygons are unchanged.

H06/H08 introduced existing human nomenclature aliases: `innerwear/* -> underlayer/*`, `body_skin/* -> arm_skin/*`. These are evaluation-time taxonomy aliases only and do **not** modify originals or reinterpret hand anatomy. H06 has 4/7, H08 2/4 polygons above the earlier 1.5% *strict automated* overshoot warning; **the user specifically accepted only H04 overshoot**. The H06/H08 reference pixels are legitimate human-traced **clipped research positives and explicit negatives** for independent evaluation. Their strict geometry signoff and all-character Golden remain separate; untraced alpha remains *unknown*, not verified negative. No eyes, brows, nose or mouth added to Minimalizer output.

## Reliable source-only and model evidence (all L02 still HOLD)

| Test | H04 | H06 | H08 | What it proves |
|---|---:|---:|---:|---|
| Source mask outerwear annotated pixels | 52,572 | 314,823 | 156,570 | Human rasterization, NOT model precision |
| Annotated foreground share | 97.82% | 55.27% | 31.96% | H06/H08 **partial** annotation only |
| Signed-source RGBA + SVG/JSON | PASS / no new SVG | PASS 7/7 | PASS 4/4 | Byte/geometry consistency |
| H04-derived raw-color trained model **leave-one-character-out IoU** | **0.0054** | **0.0326** | **0.0175** | FAIL: independent characters are not detected |
| Independently pretrained *generic clothes* Mask2Former class, **IoU on labelled pixels only** | 0.3329 (Run121 768) | 0.8315 (384) | 0.7423 (384) | Generic `clothes` **is not jacket-only** |
| Unverified/unlabelled pixels flagged as clothes | 1,556 | 159,478 | 38,129 | Cannot assert overall precision from partial labels |
| H04-adjusted unsupervised source+generic-clothes shoulder color-cluster, labelled-only IoU | 0.8624 | 0.7009 | **0.0997** | REJECT: strong H08 generalization regression |

H04-specific older two-observer soft-consensus IoU 0.863355 and the bridged H04 exclusive-owner shadow's actual pinned Phase5 graph `60848322332ac88297ef2688d06e32f17ed2b8bc` PASS 21 anchors / 13 relations **remain valid engineering results for H04 only**. Those are **not** a substitute for cross-character jacket/arm semantic quality or end-to-end Golden authorization.

The new two-training-characters/one-held-out-character source-only HistGradientBoosting benchmark: fully held-out H04 tested after training H06+H08; H06 tested after H04+H08; H08 tested after H04+H06. Source features at a 900px *diagnostic temporary analysis view*, 0.5 threshold, 15k positive and 15k presumed-negative pixels per training image, deterministic seed, no held-out manual labels in inference. **Presumed negative** in training includes unannotated opaque source and is uncertain: these metrics are diagnostic research, not an optimized benchmark. Repeat run's three NPZ files and one JSON are byte-identical. The model only trained on 3 characters and generalized poorly; no inference-time copying of polygons.

The independent pre-trained AnimeSeg was already installed locally: H04 768px (Run121), H06/H08 offline CPU 384px. Its segmentation class 10 is `clothes`, not `outerwear` or `jacket`; label-restricted H06 precision 0.996 cannot be presented as whole-image precision because 159,478 unlabeled pixels also predict clothes. One additional independent source-only color-cluster experiment was calibrated on H04 and failed on independent H08 (0.0997 labelled IoU) so is rejected. No rejected model goes to Local Worker.

## Quality gates and next requirements

- H04 exact manual reference and source-bound overshoot review: **PASS (scope-limited)**.
- H06/H08 independent manually drawn outerwear/arm references: **RECEIVED + SOURCE/SVG INTEGRITY PASS**, partial-label research evaluation ready. Any H06/H08 strict >1.5% outside-alpha still a standalone warning, not waived based on H04.
- Character-held-out **automatic jacket segmentation**: **FAIL** (raw-color LOCO IoU 0.005/0.033/0.018). Generic pretrained garment class and ad-hoc color clustering not sufficient for person-independent jacket-only ownership.
- Signed immutable masks and original artwork: **UNCHANGED**. Two-observer H04 pinned structure validation PASS belongs to old specific H04 research candidate only.
- Visual faceless output, exclusive owner tie-breaking, **fresh candidate Phase4→5 and later golden revalidation**: **NOT SATISFIED**. No production or Public C08 promotion.

**L02 formal status HOLD, production NO_GO**, even though all requested H04/H06/H08 human review data were accepted as source-bound benchmark evidence. User should not be asked to redraw H04 due the four alpha overshoots. The next engineering goal is to replace H04-specific appearance learning with an independently validated outerwear-specific semantic observer, retain safe source pixel/color evidence, then re-run the actual fully pinned Phase4→5 candidate and confirm production/Golden visually. Merely copying any user-drawn polygon into a model output is not an accepted fix.

Private JSON/SVG, signed originals, mask NPZ, per-character overlays and model inference comparisons: Drive `/chatGPT及びCodex用/Minimalizer/MinimalizerLocal_L02_ReviewedEvidence_PRIVATE_20261016.zip`. Public code/tests and source-free metrics alone go to GitHub. No user file coordinates, originals or face drawings in public artifacts.
