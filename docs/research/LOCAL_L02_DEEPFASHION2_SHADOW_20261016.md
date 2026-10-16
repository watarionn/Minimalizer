# MinimalizerLocal L02 independent outwear model shadow, 2026-10-16

**Actual independent pretrained ONNX inference: completed on H04/H06/H08. Generalized jacket quality: FAIL. L02 HOLD, Golden HOLD, production NO_GO.**

## Source and observer provenance

Following #410's generic-clothes ABSTAIN, tested real outwear-specific pretrained YOLO26s DeepFashion2 model ([model card](https://huggingface.co/HasanKabir23/Yolov26s-DeepFashion2)). Model card advertises Apache-2.0 and 13 DeepFashion2 classes including `short_sleeve_outwear=2` and `long_sleeve_outwear=3`. Downloaded **only public weights**, local file `best.onnx` SHA-256 `485bc106721febbd82fe24297e12a9fb49a435a552afff1e6b76308716555f76` (10,994,299 bytes). No package installs: existing Windows Python/onnxruntime 1.26.0; CPU only, 2 threads; PC had about 5.3 GiB free RAM at preflight. No user images sent to external inference service; all inputs came from already-signed private Drive archive `MinimalizerLocal_L02_ReviewedEvidence_PRIVATE_20261016.zip`.

Source blobs of H04/H06/H08 independently SHA-verified against previously signed sources. The CLI-shadow selects source-only RGBA, composites to white on an ephemeral analysis input, letterboxes with preserved aspect ratio to ONNX fixed `416×416`, runs the model independently, decodes NMS rows (`300×38`), 32 mask prototypes (`104×104`) and keeps only classes 2/3 at confidence ≥0.5. Reprojects to native source alpha, never creates visible pixels, and **never** inserts the held-out person's hand-labelled mask into inference. Human positives, explicit negatives and unlabelled unknown are applied only in the post-inference evaluation. No signed owner mask or production code changed.

The ONNX row/mask decoding here is a research assumption checked against observed I/O shapes and plausible detections; the upstream model's decoding implementation and image-level visualization have not passed formal independent Golden visual review. Do not elevate to production.

## Real independent outcomes

| Source | Outwear detections | Labelled-only IoU | Positive recall | Known-negative FPR | Unlabelled source predicted positive |
|---|---:|---:|---:|---:|---:|
| H04 | 0 | **0** | **0** | 0 | 0 |
| H06 | 3 | **0.627044** | 0.627044 | 0 | 3,216 |
| H08 | 2 | **0.606773** | 0.619550 | **0.219390** | 8,160 |

**FAIL:** H04 has no outerwear prediction at all. H08 has a substantial explicit non-outwear error. H06/H08 still miss source-labelled portions. `IoU` is evaluated on partial positively/negatively traced pixels only, not whole image precision; all untraced pixels remain UNKNOWN.

Two independent CPU executions produced exact source-free report JSON equality and **3/3 native prediction mask byte equality**. The public aggregate is `docs/research/LOCAL_L02_DEEPFASHION2_H04_H06_H08_AGGREGATES_20261016.json`. Original prototype runner is captured as reproducible source-only research code at `tools/research/local_l02_deepfashion2_shadow.py`, with **7/7 synthetic mask/alpha/invalid-input tests PASS** in isolated test runtime; full repo CI not claimed.

Private predictions and source-free report are written into existing Google Drive desktop mounted `chatGPT及びCodex用/Minimalizer/MinimalizerLocal_L02_DeepFashion2_OUTERWEAR_SHADOW_PRIVATE_20261016.zip`; second write hash `fb5e2e788fbbca03c492d30883e26624115be4ca8bb345cf8f43fef4d6c4aa04`. **Drive cloud-provider read-after-write is not yet confirmed; only PC-mounted-drive content was verified.** Do not describe it as cloud-sync complete until verified by Drive connector. The source-free report payload SHA is `3476993af9ff78553b056ce7b4d30f7ae65885eec8a7a58141b2cf2fe046a6f0`.

## Next steps without hiding first failure

- Independent generalization blocker is now backed by **two distinct negative trials**: source-color LOCO fails, genuine pretrained outerwear-specific YOLO26 model fails H04 and H08. Neither can become jacket-owner authority.
- Consider a second class-aware human parsing model only after licensing/weight SHA/runtime preflight. Require native signed-source H04/H06/H08 observed improvements without trial-by-trial overfit; do not loosen thresholds simply to promote.
- Keep L03 exclusive Phase4→5 actual pinned candidate replay, L04 Stage8 source budget/Chromium DPR1/DPR2, L06 Golden and L08 user iPhone acceptance blocked on successful L02 semantic and full visual quality. Safely parallel L07 PWA read-only audits are permitted.
- Continue strict faceless output, source-only raster, no generative fill, H04 accepted alpha exception ONLY on the exact approved submitted trace, H06/H08 alpha overshoot not waived, private/public separation.
