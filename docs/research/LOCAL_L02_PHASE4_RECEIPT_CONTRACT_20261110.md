# L02 candidate-specific Phase4 receipt contract

`tools/research/verify_local_l02_phase4_receipt.py` validates the independent
receipt after a frozen candidate has been reviewed. It reads hashes and review
attestations only; it never reads source pixels, masks, labels, or NPZ arrays.

The receipt must use schema
`minimalizer/l02/phase4-independent-review/v1`, set `phase4` to `PASS`, include
a non-empty reviewer ID and timezone-aware `reviewed_at_utc`, and set the
global signature, unseen-data, pre-inference-label-unavailable, independence,
semantic-review, unknown-is-unknown, and frozen-before-scoring flags to the
required values. The two inference-leak flags must be explicitly `false`.

Each of H04, H06, and H08 must include the pinned signed source SHA, the exact
candidate-array SHA from `SAPIENS2_CANDIDATE_FREEZE_RECEIPT.json`, and positive
checks for garment preservation, justified wrong-owner removal, exclusive
sleeve recovery ownership, occlusion/critical-part preservation, visual
acceptability, and unknown-not-negative handling.

The verifier can return `Phase4: PASS` only. Its output always remains
`Phase5: NO_GO`, `Golden: HOLD`, and `production: NO_GO`; later promotion is a
separate gate.
