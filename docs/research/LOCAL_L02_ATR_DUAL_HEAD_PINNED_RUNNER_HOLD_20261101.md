# Lane A L02: ATR18 dual-head signed-source runner (2026-11-01)

**Research implementation only. No signed-image ATR inference has been completed; no P0/P1 repair or owner promotion. L02 HOLD / Phase4 FAIL / L03 NO_GO / Golden HOLD / production NO_GO.**

## Purpose and bounded implementation

The existing ATR18 postscore-only head-disagreement helper accepted two class maps, but there was no authenticated execution path proving that `logits` and `parsing_logits` came from **the same model snapshot, source image and ONNX inference call**. That missing provenance prevents a defensible H06 bag/arm comparison.

The research-only `run_offline_atr_dual_head_observer` now authenticates the encoded signed source and decoded RGBA against external SHA-256 pins, then authenticates the exact pinned ATR18 INT8 ONNX bytes in an immutable in-memory snapshot. It checks CPU provider, input name, **both** output names, shape (1,18,512,512), numeric finiteness, and source-alpha clipping. It obtains both heads in a **single** `session.run(['logits','parsing_logits'], ...)` and produces separately hashed private class maps and a source-free disagreement receipt. No human annotations, owner masks, threshold fitting or pixel generation enter inference.

The preexisting `run_offline_atr_bag_observer` retains its raw `logits` API and v1 receipt schema. The dual-head runner cannot select the better head after looking at human labels; `head_selection_authorized=False`. Model identity is the pinned `pirocheto/schp-atr-18` revision `a54fa65e7e4f27f21011f652ffc0053ebb24b292`, ONNX SHA-256 `4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5`, 69,141,996 bytes. See the existing ATR observer licence-gate document for the unresolved training-data rights.

## Verification and honest limits

Source-free isolated execution using a fake ONNX Runtime and synthetic signed inputs exercised: same-session provenance, old single-head compatibility, wrong checkpoint refusal, absent refined output refusal, and malformed refined output refusal. **5/5 isolated tests passed** with stand-in source validation. These are not an exact full-PR QA run, actual ATR ONNX execution, signed H04/H06/H08 comparison, independent unseen validation, Phase4 quality PASS, or a licence clearance.

The real ATR model was not available in the authenticated local runtime or in the searched canonical Drive files in this run. No private model prediction was produced, uploaded, or claimed cloud-preserved. No P0/P1 improvement is accepted: **0/0**. H04/H06/H08 remain **3 unresolved major cases**.

## Next required engineering gate

Obtain the exact pinned checkpoint through a permitted local route, independently SHA-check it, then execute the two heads against the signed source RGB/alpha without human labels. Save both class maps and receipt to the existing non-shared `chatGPT及びCodex用/Minimalizer/10_Artifact_Library/03_Private_Research_Evidence` and verify remote bytes before postscore. Measure H06 bag/underlayer/arm FP separately from unknown, H08 sleeve/arm retention and H04 regression. Only a source-only exclusive-owner repair passing critical-part and topology gates can advance Phase4. Unseen signed blind evaluation, formal QA, dataset rights and human Golden acceptance remain outstanding.

**No changes to B L04/L07, Public/C08, LocalWorker production or Golden.**