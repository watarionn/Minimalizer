# MinimalizerLocal L02 — Unseen-Character Transfer Probe / 2026-10-15

**Scope:** the next research step after H04 human jacket reference v1 and non-destructive jacket shadow PR #402. **Engineering experiment COMPLETE; independent semantic generalization NOT PASSED; L02 milestone HOLD; production NO-GO.**

## Source and version boundary

- Trained only on the user's H04 manual full-body source-aligned reference. H04 source SHA: `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`. H04 is not an external hold-out case.
- Run105 private source18 archive SHA: `d652f09625c08c25d88ccf312f408af762982554b30453e42ecb5076cbe3a8eb`. Checked all **18/18** source-file raw SHA256 against the archive's embedded manifest; archive's `selection_approval` is **PENDING**, so source integrity does NOT establish independent human label quality.
- Target images: H01–H18, excluding training H04 = **17 never-trained source images**. No validated semantic mask / independent jacket-shaped human trace for any of these 17 in the available materials.
- Classifier version: `tools/research/local_l02_manual_supervised_shadow.py` from the merged #402 / main `3ed74b54b3afc0d7b56662b1491eef0c689a9845`; unchanged H04-trained gradient booster parameters and decision threshold `0.50` (previously tuned using H04, so not a general-purpose threshold).
- The previous H04 pinned actual Phase5 graph check **PASSED** with blob `60848322332ac88297ef2688d06e32f17ed2b8bc`; this run does **not** run that graph for the 17 targets because no separate source-authenticated Phase4 part-owner masks exist for them.
- Public deliverables contain source-free code, synthetic tests, numeric metrics and this report. PRIVATE deliverables contain original pictures, unapproved overlays, classifier-trained research runner and blank independent-label intake. No source images, source geometry or learned model weights are put in public GitHub.

## Experiment (not quality scoring)

1. Verify the raw H04 and 17 target source byte checksums **before** loading and using images.
2. Train once only on existing signed-source-identical H04 pixels and its user-provided jacket region labels. No target pixels or annotations influence fitted weights, but classifier design and threshold were selected after viewing H04.
3. For 17 other images, inspect transparency. H13, H15, H16 have background broadly opaque and touching the boundary; fail closed and **ABSTAIN**.
4. For the remaining 14, observe *raw model responses* on source RGBA foreground sample values. For large images sample **existing pixels at a fixed stride** to cap longest edge at 800 pixels. This changes local image feature scale and must **NOT** be mistaken for native-resolution anatomical segmentation, source-exact topology or allowed Phase4 outputs.
5. Never create owner masks, source-traced polygon shapes or call the result an approved jacket. Do not compute or imply precision, recall, IoU or per-character quality without an **independent target label**.
6. A native pixel-resolution spot-check on H06/H08/H17 specifically measures scale dependence of the raw response. These are still unmasked raw probes only.

## Observations

Raw positive response fraction among the source's sampled nontransparent pixels (NOT clothing accuracy):

| Case | Status | Raw positive fraction |
|---|---|---:|
| H01 | RAW only | 1.16% |
| H02 | RAW only | 0.10% |
| H03 | RAW only | 25.96% |
| H05 | RAW only | 3.61% |
| H06 | RAW only | 2.37% |
| H07 | RAW only | 1.38% |
| H08 | RAW only | 7.93% |
| H09 | RAW only | 13.61% |
| H10 | RAW only | 0.00% |
| H11 | RAW only | 9.63% |
| H12 | RAW only | 0.01% |
| H13 | ABSTAIN | — |
| H14 | RAW only | 1.59% |
| H15 | ABSTAIN | — |
| H16 | ABSTAIN | — |
| H17 | RAW only | 11.71% |
| H18 | RAW only | 0.93% |

- H03: visibly broad responses on a large skirt, which is not evidence of blazer detection; diagnostic warning of wrong class/overgeneralization.
- H06: a conspicuous long coat, yet raw positive fraction is just **2.37%** at sampled scale and **3.70%** at full pixel scale; no claim of recall can be made without a separate signed jacket/coat label.
- H11: raw model highlights the legs/boots in the source. A human-visible negative control for upper-body jacket ownership.
- H13/H15/H16: **3/17 ABSTAIN**, opaque background violates the foreground-only assumption.
- Native-scale spot check: H08 **7.93% sampled vs 12.39% native**; H17 **11.71% sampled vs 15.17% native**. Feature scale shifts enough to invalidate treating thumbnail raw results as equivalent to source-resolution predictions.

**Therefore:** the H04 single-reference model is **NOT ready for general adoption**. The visual tests reveal domain generalization and scale-control weaknesses. This does not contradict the earlier H04-only IoU improvement, but it rules out using that improvement as proof of external-character performance.

## Verification and fail-closed safety

- 15/15 new synthetic tests PASS: original SHA tamper, alpha/background guard, malformed input/probabilities, no invented semantic labels, no owner masks, false promotion refusal.
- 16/16 previous H04 research tests PASS; combined **31/31**.
- Two independent executions of the entire 17-target loop generated **20/20 identical byte-level outputs**, comprising 17 case diagnostic panels, one contact image and two metric JSON files (after native-scale addendum the public metrics file is updated, and its final SHA is recorded in the deliverables).
- 18/18 original raw source SHA matches the private Run105 manifest; the manuscript's approval status is **PENDING**.
- **0/17** unseen signed semantic labels. Semantic precision/recall/IoU intentionally `null`; Phase4 output candidates created **0**; signed original source and H04 masks unchanged; production Worker/Public unchanged.

## Next gates to actually complete L02

1. Independent user/reference manual annotations for at least **H06** (contrasting tan long coat) and **H08** (pink jacket) in Reference Shape Editor. Exact original bytes and blank review form are in the PRIVATE archive; do not use our green raw response as a target.
2. Establish source-aligned independently reviewed garment *and* arm/hair semantic masks for representative jacket, sleeve/skin overlap and difficult non-jacket examples. In this set, H03 and H11 should function as negative controls. Authenticate every imported mask against the original SHA and source pixel coordinate space.
3. Fix scale robustness and extend semantic training to more than one annotated character, with leave-one-character-out validation. Freeze hyperparameters before holdout; H04-spatial-fold scores are no substitute for this.
4. Only after independent cross-image pixel/occlusion quality gates pass may candidate masks be considered for signed Phase4→5 integration and Golden human review. Keep original signed masks immutable, unresolved overlapping owner memberships isolated from published renderers, C03 Stage8 and C04 Golden HOLD.

**Decision:** `UNSEEN_PROBE_EXECUTED / EXTERNAL_SEMANTIC_GENERALIZATION_FAIL_EVIDENCE / L02_HOLD / RELEASE_NO_GO`.
