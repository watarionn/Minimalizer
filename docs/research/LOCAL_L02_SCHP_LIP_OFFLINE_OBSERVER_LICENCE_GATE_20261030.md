# L02 SCHP-LIP independent subpart observer: offline research-only integration (2026-10-30)

## Verified sources and licensing gate

- Official LIP dataset provider: https://sysu-hcp.net/resources/datasets/index.html explicitly grants use for **non-commercial** academic/personal research and experimentation. The Hugging Face model card `pirocheto/schp-lip-20` reports MIT for the model packaging, but this does **not** independently clear rights in the LIP-trained weights for commercial deployment.
- Model and class source: https://huggingface.co/pirocheto/schp-lip-20 and https://github.com/pirocheto/schp-human-parsing. LIP classes: coat=7, upper-clothes=5, left/right arm=14/15, hair=2. These labels are *possible* positive semantic observations, not anime accuracy evidence.
- Upstream processor: https://huggingface.co/pirocheto/schp-lip-20/blob/a0415db02764ae31c416e8d103b8850569be63f8/image_processing_schp.py; 473x473 bilinear RGB, mean [0.406,0.456,0.485], std [0.225,0.224,0.229]. For transparent signed art the new research module explicitly predeclares a white RGBA composite. That is a research-domain choice, **not** an upstream-proven training equivalent.
- Upstream ONNX option: `onnx/schp-lip-20-int8-static.onnx`; do not treat a file name or advertised 99.09% PyTorch pixel agreement as a verified model SHA or anime-domain quality result. Actual weight bytes and exact revision must be authenticated separately.

## Integrated Lane A source-only code

- `tools/research/local_l02_schp_lip_observer_research.py` runs only with external SHA-256 pins for the encoded signed source, decoded RGBA, and local ONNX checkpoint, plus a 40-hex model revision. It independently decodes and verifies signed source bytes, hashes the local model before importing ONNX Runtime, restricts the session to CPU, checks LIP20 logits, and returns only a private class-map array plus source-free counts and SHA receipt.
- The module **never** loads reviewed human masks, edits owner assignments, sends private data to a hosted service, auto-downloads weights, or promotes Phase4/Golden/production. The returned class map must be stored only in the existing non-shared Drive research evidence folder by the authorized private caller, followed by cloud read-after-write.
- `tests/test_local_l02_schp_lip_observer_research.py`: six source-free tests cover signed-byte mismatch, alpha-composite preprocessing, invalid logits, alpha eligibility, wrong model pin and a fake offline CPU session. Local isolated run: **6/6 PASS**, compileall PASS. No actual ONNX model execution or signed H04/H06/H08 inference occurred in this run.
- Both files were committed to A-only Draft PR #445. Remote Git blob readback matches locally tested files exactly: module `f47553e1578b245199271a6c5618462d29bd7f41`, tests `8daeef5da7e3b288e556dc5dca67a403bdbaaa24`. This is an engineering precondition, **not a P0 image fix**.

## Next decisive signed-image experiment (not performed)

1. Obtain and independently pin the exact model revision, ONNX bytes SHA-256, model/weights terms, and allowed research-only use. No production deployment without separate LIP training-data rights resolution.
2. Run this observer **offline** with existing signed H04/H06/H08 source RGB/alpha and independent external source SHA pins. Freeze private class maps and their SHA before opening any human-reviewed masks. Store private output only in the canonical non-shared Drive evidence folder and verify cloud readback.
3. Independently postscore H06 known underlayer FP (historical strict 1,077px), H06 reviewed missing outerwear (20,803px), H08 missing outerwear (19,309px), and H08 known-arm false ownership. Check H04 regression. Do not treat unknown pixels as negatives.
4. Only if independently positive subpart evidence reduces major P0 defects without introducing arm/underlayer/critical-part or 4/8-connectivity regressions, implement an *independent* source-only owner proposal, run exact-PR-head Phase4 QA and signed replay, then genuinely unseen signed blind evaluation. Do not use the existing class32-only postcondition to authorize new classes without a reviewed, separate contract.

## Status

**Accepted P0 fixes 0; P1 fixes 0; H04/H06/H08 unresolved 3.** This run adds source-only research code/tests and a licence-gated observer path, not signed-image improvement. PR #445 remains Draft, no merge, main unchanged. Exact PR-head full QA, signed real inference, Phase4 critical-part/semantic PASS, unseen blind, owner-PC QA and Golden approval remain pending. iPhone acceptance is post-deployment. **L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.** No Lane B, Public/C08, LocalWorker production or Golden changes.

## 2026-10-30 official ONNX checkpoint provenance correction

The model-card's original image-processor revision `a0415db02764ae31c416e8d103b8850569be63f8` predates the ONNX addition. It is **not** an appropriate revision pin for the ONNX checkpoint. The official Hugging Face model commit `3cc2b2d00b16840652c1b7845fd78466dae7f157` added `onnx/schp-lip-20-int8-static.onnx`, with Git LFS SHA-256 `871c9e209dc67d6be61c73dcc79cb49e638fcf5bbc35a19b4c7429eba0bfc046` and exact size **68,314,352 bytes**. Both the immutable commit diff and current file's Xet pointer independently display that SHA. Sources: https://huggingface.co/pirocheto/schp-lip-20/commit/3cc2b2d00b16840652c1b7845fd78466dae7f157 and https://huggingface.co/pirocheto/schp-lip-20/blob/main/onnx/schp-lip-20-int8-static.onnx .

**Concrete code correction:** the offline observer now rejects a caller-provided arbitrary 40-hex revision or SHA, and rejects unexpected checkpoint filename/byte size before hashing or ONNX Runtime import. It accepts only the public exact commit+SHA+size+filename tuple, then independently streams SHA-256 from local bytes. Source-free fake-session tests explicitly override only the pinned hash and size inside the test process; that synthetic override is never a release path. This closes a provenance/identity ambiguity, not an image-quality defect. No checkpoint was downloaded, no signed private image was inferred, and no new owner was promoted in this checkpoint. Repository-level runtime QA remains pending; source-free test edits alone are not PASS evidence.

The model's published labels distinguish coat and arms but **do not include a dedicated underlayer/underwear class**. Even successful inference would not by itself prove H06 underlayer-vs-outerwear correctness; explicit abstention and independently verified postscore remain required. LIP training-data noncommercial restriction and production licensing HOLD remain unchanged. **Accepted P0/P1 0/0; H04/H06/H08 unresolved 3; Phase4 FAIL / L02 HOLD / L03 NO_GO / Golden HOLD / production NO_GO.**
