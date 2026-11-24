# Lane A L02: ATR18 exact-checkpoint local acquisition gate (2026-11-01)

**Research-only / NOT an image-quality fix.** H04/H06/H08 P0/P1 accepted improvements remain **0/0**, with **3 unresolved major cases**. L02 HOLD, Phase4 FAIL, L03 NO_GO, Golden HOLD and production NO_GO remain in force.

## What was unblocked in source code

The authenticated ATR18 dual-head runner in PR #447 requires a local 69,141,996-byte ONNX checkpoint, but the exact checkpoint had not been acquired. The public upstream file was independently located in the **`onnx/` subdirectory** of the pinned revision, not at the model repository root:

- Public source: https://huggingface.co/pirocheto/schp-atr-18/blob/a54fa65e7e4f27f21011f652ffc0053ebb24b292/onnx/schp-atr-18-int8-static.onnx
- Immutable revision: `a54fa65e7e4f27f21011f652ffc0053ebb24b292`
- File SHA-256: `4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5`
- Size: `69,141,996` bytes.

The source-free `tools/research/local_l02_atr_checkpoint_fetch_research.py` uses the pinned HTTPS `resolve/<revision>/onnx/<filename>` endpoint. It only accepts an existing local directory outside any Git checkout/worktree, downloads to a temporary file with a strict byte ceiling, verifies SHA-256 and size, and publishes without replacing an existing file. It never uploads a signed source, mask or model output. A verified existing checkpoint is reused without network access. No third-party image inference is performed.

## Actual verification and limits

The downloader's isolated, offline regression covered successful authenticated receipt, idempotent reuse, wrong-byte rejection and cleanup, existing-file preservation, and worktree-path rejection. **4/4 synthetic tests passed locally**. These tests do not constitute ONNX inference, image-quality validation, or full exact-PR-head repository QA.

The actual 69 MB public checkpoint download was attempted through the available container downloader and Hugging Face client, but did **not** complete: the direct download failed, and the local Python route reported DNS/name-resolution failure. **No model bytes were acquired or SHA-verified locally, no H04/H06/H08 ATR class maps were generated, and no private Drive write/readback occurred.** The acquisition helper has not been exercised against the real endpoint.

## Next gate, without user intervention

Use the source-free helper on an authorized networked environment with a private local model-cache directory outside Git. Verify the full model SHA, then run the existing pinned ATR dual-head observer locally on authenticated signed H04/H06/H08 source bytes. Preserve raw and refined class maps in the existing non-shared Drive evidence folder and cloud read-after-write before postscore; compare bag/arm/underlayer false ownership, H08 sleeve loss, and H04 regression. No model head may be selected using known human labels. Dataset rights, Phase4 exclusive-owner/critical-part PASS, true unseen blind, exact-PR QA and Golden approval remain separate gates.

B L04/L07, Public/C08, LocalWorker production and Golden were not modified.
