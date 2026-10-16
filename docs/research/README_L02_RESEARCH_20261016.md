# Minimalizer Local L02 research handoff, 2026-10-16

**Formal L02 HOLD; production NO_GO.**  The provided sources are private, and the public code here contains no images, hand polygon coordinates or masks. The H04 alpha overshoot exception is narrowly pinned to the exact user-reviewed H04 original and full-trace digest, not a global acceptance-threshold relaxation.

All commands assume this research code is placed in `watarionn/Minimalizer` at the specified `tools/research`, `tests` and `docs/research` paths. `benchmark_leave_character_out.py` imports the pre-existing `tools/research/local_l02_manual_supervised_shadow.py` introduced in PR #402.

Run fail-closed synthetic regression tests: `python tests/test_local_l02_manual_intake.py`, `python tests/test_reviewed_annotation_intake.py`, `python tests/test_local_l02_reviewed_transfer_benchmark.py`. Total **52/52 PASS** in the 2026-10-16 development sandbox.

With authenticated private inputs in a directory, run:
`python tools/research/verify_reviewed_annotations.py <private-input-dir> <private-output-dir>`
`python tools/research/benchmark_leave_character_out.py <private-input-dir> <private-output-dir>`

Original private names used: `H04_original_signed_trace (1).json`, `H06_trace.json`, `H06_trace.svg`, `H08_trace.json`, `H08_trace.svg`. The tool validates signed source bytes and SVG/JSON polygon parity. Never commit these files or their generated NPZs to GitHub.

`tools/research/color_cluster_shadow.py` is retained as a reproducible **REJECTED** H04-adjusted experiment. Do not wire it into production. H06/H08's partial annotations are not a fully signed segmentation and unlabelled pixels must remain `unknown` for trustworthy metrics.

## 2026-10-16 verified continuation after PR #408

The previously missing exact signed H04/H06/H08 private review bundle was located via the established `chatGPT及びCodex用/Minimalizer` Drive folder. The explicitly-known-negative LOCO diagnostic has now been executed twice with byte-identical outputs, using the same GitHub-canonical #407 baseline functions as #408. Details and aggregate results are in [LOCAL_L02_KNOWN_ONLY_REAL_HOLDOUT_20261016.md](LOCAL_L02_KNOWN_ONLY_REAL_HOLDOUT_20261016.md). Three labelled-only IoUs: **H04 0.218283, H06 0.164998, H08 0.029907**; **all three still FAIL independent-character quality**. The private prediction artifact is on Drive with SHA-256 `c2133af02b78b029ff5eb7467dab05b96a847f847f6800a825d9e7927308cbd3`. L02/Golden HOLD and Local/Public NO_GO remain unchanged. Do not re-open the already settled H04 overshoot review or treat H06/H08 partially labelled unknown pixels as negatives.


## 2026-10-16 continuation after #409: PR #410 and #411 (merged)

- [PR #410](https://github.com/watarionn/Minimalizer/pull/410), main `5072e8fe1c059addc3dbaef2e1a4f6120854cb4d`: source-only outerwear taxonomy gate. Generic AnimeSeg class `clothes` (H06/H08) is not jacket semantics; explicit `ABSTAIN_NO_OUTERWEAR_CLASS`, no owner promotion. Signed-source independent replay: labelled IoU H06 0.831542 and H08 0.742307, with unknown predictions 159478/38129 px respectively. 64 targeted+existing synthetic tests passed; no model rollout.
- [PR #411](https://github.com/watarionn/Minimalizer/pull/411), main `468b389dca40ec9f823b64bce259e75d7315f9ec`: **real independent pretrained outerwear** YOLO26s DeepFashion2 (Apache-2.0 model card), ONNX SHA `485bc106721febbd82fe24297e12a9fb49a435a552afff1e6b76308716555f76`, 416px white RGBA-composited letterbox, CPU-only. Exact signed-source H04/H06/H08 labelled-only IoU **0.000000 / 0.627044 / 0.606773**, outwear detections **0 / 3 / 2**; H08 known-negative FP 0.219390. All 3 prediction masks and source-free report identical on two independent runs. 7 decoder synthetic tests passed; independent Golden visual review and full repository CI not run. The ONNX mask-decoding assumption remains research only.
- Only source-free research code/tests/metrics/docs merged into main. Signed image pixels, hand drawings, mask NPZ and candidate visual exports remain private. Local Worker, Public/C08, scheduled campaign and release flags unchanged. **L02 HOLD / Golden HOLD / production NO_GO**. The private evidence ZIP `MinimalizerLocal_L02_DeepFashion2_OUTERWEAR_SHADOW_PRIVATE_20261016.zip` was written and re-read from the PC's existing mounted Drive folder; the Drive cloud connector did **not** yet return that new file, so do not say cloud sync verified. Keep the verified PC mounted file until provider read-after-write succeeds.
- **Next actual quality step**: verify licensing, model SHA and bounded runtime for another truly garment-specific independent observer (e.g. `sayeed99/segformer-b2-fashion`, licence unresolved); infer signed H04/H06/H08 without user polygons, preserve explicit known negative versus unknown, and require actual cross-character quality before creating an exclusive Phase4 owner candidate. If rejected, retain negative evidence and do not falsely promote Phase4→5 or Golden. In parallel, non-destructive L07 SW/Origin/Tailscale audits are allowed. No new per-case threshold tuning to hide H04 failure.
