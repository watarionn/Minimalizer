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
