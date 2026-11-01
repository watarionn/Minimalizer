# Lane A L02: pinned SCHP-ATR18 bag/arm observer (2026-11-01)

**Status: research-only source-free implementation, NOT signed-image inference or owner repair. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Why this independent observation is needed

H06's frozen Run30 class25 bag/coat disagreement includes 22,087 tentative bag pixels, of which 9,913 overlap the human-reviewed outerwear reference and 12,174 are unlabeled. The class25 prediction is not ground truth. The existing isolated SCHP-LIP20 observer distinguishes coat, glove and arms but has no bag class. ATR18 independently offers `16=bag`, `14/15=arms`, `4=upper-clothes`, `6=pants` and `2=hair`. **ATR18 does not have a coat or underlayer class**, so neither ATR nor LIP alone can resolve coat-versus-underlayer or approve owner reassignment. These observers share an architecture and are not automatically statistically independent.

## Exact upstream model identity

- Model card: https://huggingface.co/pirocheto/schp-atr-18
- Initial ONNX checkpoint commit: https://huggingface.co/pirocheto/schp-atr-18/commit/a54fa65e7e4f27f21011f652ffc0053ebb24b292
- Exact `onnx/schp-atr-18-int8-static.onnx` LFS SHA-256: `4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5`, size `69,141,996` bytes. These are the upstream commit's LFS pointer, **not** a locally downloaded checkpoint SHA.
- Upstream ATR processor: 512x512 bilinear, normalized RGB with mean `[.406,.456,.485]`, std `[.225,.224,.229]`. Transparent source is composited on white as an explicit research choice, not a proven domain-equivalent preprocessing step.
- Hugging Face lists the model as MIT. **ATR training dataset and original-image rights have not been independently cleared for production**, regardless of model-card metadata. No production promotion or commercial licence claim.

## Implementation and strict boundaries

`tools/research/local_l02_schp_atr_bag_observer_research.py` reuses the isolated LIP observer's signed encoded-source/RGBA verification, then checks the immutable ATR revision, filename, exact byte count and full ONNX SHA before running a CPU-only, in-memory model snapshot. It validates the expected 18-class logits and alpha-clips the private class IDs. It emits only a private class array to the caller and a source-free receipt; it has **no** human-mask or owner input and does not modify any pixel, Golden or production path. No network downloads or remote inference occur. Private class maps must be stored in the existing non-shared Drive evidence folder with cloud read-after-write if the exact local model becomes available.

`tests/test_local_l02_schp_atr_bag_observer_research.py` adds 4 synthetic fail-closed checks. The module and tests were tested in an isolated local mirror with a minimal stand-in for the existing LIP source verifier: 4/4 PASS and compileall PASS. **That is not an exact full PR-head run or full four-stage repository QA.** The actual ATR ONNX model was **not** downloaded or executed; no signed H04/H06/H08 ATR prediction was produced. Existing H04/H06/H08 private archive SHA pins were independently rechecked on 2026-11-01, but those source and label bytes are not in this PR.

## Next decisive experiment

Obtain the exact pinned ONNX locally through an authorized route, verify its bytes and dataset-use rights, then run H04/H06/H08 offline on externally pinned signed source RGB/alpha. Freeze each model prediction and cloud-preserve its private class map **before** opening human labels. Postscore ATR bag versus existing class25 and LIP coat/arm, with known negative versus unknown separated. H06 underlayer/arm false ownership and H08 missing sleeves remain the priority. Do not OR/AND model classes into an owner; only a separate source-only proposal with exclusive owner, connectivity, critical-part retention and no regression could be eligible for Phase4, followed by unseen signed blind and canonical QA.

**Accepted P0 improvements 0; P1 improvements 0; unresolved H04/H06/H08 3. New A-only observer and tests, no merge.** B L04/L07, Public/C08, LocalWorker production and Golden unchanged.
