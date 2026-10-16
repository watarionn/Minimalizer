# MinimalizerLocal L02: outerwear-specific observer admission (2026-10-16)

**Research engineering PASS, outerwear model quality NOT ESTABLISHED. L02 HOLD / Golden HOLD / production NO_GO.**

## Motivation

Merged PR #409 established that explicitly known-negative LOCO learning improves upon PR #407's presumed-negative baseline, but H04/H06/H08 independent-character outerwear quality remains unacceptable. Neither human-drawn polygons nor generic AnimeSeg class 10 `clothes` may be silently promoted as automatic jacket semantic truth.

This continuation adds a source-bound, taxonomy-exact guard at `tools/research/local_l02_outerwear_observer_gate.py`. The observer API accepts only a signed source alpha and independently emitted class-map, with model/source/map SHA and declared class names. If there is no *explicit* `jacket`, `coat`, or short/long sleeved `outwear` class, it returns `ABSTAIN_NO_OUTERWEAR_CLASS`. Generic `clothes`, `upper-clothes`, `sleeve`, `collar` and other garment/part names alone do not establish an outerwear class. Even a fine-grained class-map is **research candidate only**; the API never grants owner promotion. Human positives/negatives are only passed to a separate evaluation routine, where unlabelled signed source pixels stay unknown.

## Verified real-image negative control

Previously signed private H06/H08 ReferenceShapeEditor v1.1 JSON/SVG were verified against exact source SHA through the existing reviewed intake. Previously executed Run121 offline AnimeSeg class-map PNGs were verified against a private archive member hash manifest and source dimensions. **This is a replay of existing model results, not a new model inference.**

| Source | Generic class10 IoU on labelled source pixels | Known-negative FP rate | Predicted generic clothes on unannotated source pixels | Owner admission |
|---|---:|---:|---:|---|
| H06 | 0.831542 | 0.054042 | 159478 | ABSTAIN |
| H08 | 0.742307 | 0.000000 | 38129 | ABSTAIN |

High labelled-only IoU cannot establish jacket-versus-underlayer instance ownership. Partial untraced source areas are not negatives; do not claim whole-image precision. H04 is explicitly `NOT_RUN` because this private H06/H08 archive contains no H04 class-map. Run twice with byte-identical source-free aggregate JSON SHA-256: `6ff755a305120fc1948eb33fe8ee1694ce233cfb9b668b428666cbefd409e7e5`.

Test command: `python tests/test_local_l02_outerwear_observer_gate.py`. Replay command, after securely preparing the five already-validated H04/H06/H08 input files: `python tools/research/run_local_l02_animeseg_taxonomy_control.py <private_json_directory> <private_class_map_zip> <private_result_json>`. Existing `verify_reviewed_annotations.py` enforces H06/H08 SVG parity and signed underlay SHA. Results: **64/64 targeted and existing synthetic tests PASS** in isolated development environment. No repository-wide CI claim.

Only these public research scripts, synthetic tests, and source-free metrics go to GitHub. Signed source and human polygons remain in the existing private Drive folder `chatGPT及びCodex用/Minimalizer`. No Worker/PWA/Public changes, no generated image pixels, no facial feature output.

## Independently pretrained outerwear model evaluation targets

Model *metadata only* has been researched. No new weights installed or private images sent to external inference services.

- [HasanKabir23/Yolov26s-DeepFashion2](https://huggingface.co/HasanKabir23/Yolov26s-DeepFashion2) advertises distinct long/short-sleeve-outwear instance segmentation classes, ONNX and Apache 2.0. It is a plausible first **research** candidate, but its real-fashion training and model card scores are not proof of accuracy on anime characters.
- [sayeed99/segformer-b2-fashion](https://huggingface.co/sayeed99/segformer-b2-fashion) declares `jacket` and `coat` semantic classes, but its licence and exact weight/source hashes must be checked before use.
- [mattmdjaga/segformer_b2_clothes](https://huggingface.co/mattmdjaga/segformer_b2_clothes) reports generic `Upper-clothes` without a separate outerwear label, so it cannot by itself qualify.

## Remaining quality steps, do not fabricate PASS

1. Verify provenance/licence and bounded CPU runtime of genuinely fine-grained independent outwear model, pin model SHA, perform **actual** source-only inference on original H04/H06/H08, verify no held-out polygon at inference.
2. Compare positive, explicitly labelled negative, and unknown separately on each character with deterministic replays. No hold-out threshold tuning on these three cases. Reject poor transfer and preserve unknown instead of autoassigning.
3. Only for a successful independently validated observer, propose exclusive Phase4 owner repair without changing signed raw Phase4 masks, then actual pinned Phase4→5 graph, attachment and occlusion, source Stage8 ring budget, SVG/Chromium DPR1/DPR2, fresh faceless visual Golden.
4. L06 human Golden approval and L08 iPhone user acceptance cannot be auto-authorized. L02/Golden/Production remain HOLD/NO_GO; scheduled Public/C08 campaign stays unchanged.
