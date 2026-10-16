# Local L02: human-known-negative LOCO control (2026-10-16)

**Research-only, not a new outerwear observer. L02 HOLD, Golden HOLD, production NO_GO.**

PR #407's original leave-one-character-out training treated every non-jacket opaque pixel as a **presumed negative** even where H06/H08 human annotations explicitly left source pixels **unknown**. This can mix possible true outerwear into the negative class. The original low-IoU result remains an accurate record of that experiment but does not isolate generalization error from training-label noise.

A separately named control at `tools/research/benchmark_known_label_loco.py` now trains the same pinned source-feature model using **only human-explicit non-outerwear categories as negatives**. Human-visible outerwear is positive; untraced source-alpha is neither class. Three LOCO folds preserve disjoint training characters. Inference uses only signed-source image features and alpha, not the held-out user's polygon vertices or segmentation masks. Reporting maintains a distinction between labelled-pixel IoU and unknown-pixel predictions. The pre-existing model parameters were earlier explored on H04 and are **not** independently calibrated.

From repository root run:

```sh
python tests/test_local_l02_known_label_loco.py
python tools/research/benchmark_known_label_loco.py <private_input_dir> <private_output_dir>
```

The private input directory must contain the exact five signed H04/H06/H08 human JSON/SVG filenames described in `docs/research/README_L02_RESEARCH_20261016.md`. Source SHA, original image extent and H06/H08 JSON/SVG parity are validated by the existing private intake. The outputs `*_KNOWN_NEGATIVE_LOCO_PRIVATE.npz` and `L02_KNOWN_NEGATIVE_LOCO_PRIVATE.json` stay private, **never in GitHub**.

The synthetic negative-control suite checks exclusive positive/negative/unknown partitioning, rejects untraced pixels relabelled as known, abstains on missing class support, excludes held-out cases from training and checks deterministic replays. Initial 10/10 tests passed in the isolated development environment with the relevant PR #407 sampling/prediction/scoring functions reproduced; CI/repository integration is separately required.

**Real H04/H06/H08 evaluation is completed as a separate, failing research result (2026-10-16).** Using only human-explicit negative pixels, new labelled-only IoUs were **H04 0.218283 / H06 0.164998 / H08 0.029907**, versus original assumed-negative scores 0.005419 / 0.032561 / 0.017511. Despite the improvement, H04/H08 known-negative FP rates are **0.951932 / 0.515640**, with low H06/H08 recall; independent outerwear quality **FAIL**. Two replays are byte-identical, private artifacts are on Drive, and public source-free metrics are recorded in [real benchmark report](LOCAL_L02_KNOWN_ONLY_REAL_HOLDOUT_20261016.md). This does not replace an independent outerwear semantic observer, exclusive owner repair, actual Phase4→5 replay, Stage8 budget, faceless Golden human review, or iPhone acceptance. The original PR #407 benchmark is untouched. Local Worker, Public, PWA, canonical signed masks and production release flags remain unchanged.
