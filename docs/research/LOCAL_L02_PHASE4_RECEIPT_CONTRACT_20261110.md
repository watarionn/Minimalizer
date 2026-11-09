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
regression acceptability, and unknown-not-negative handling.

The human form must keep these two questions separate:

- `visual_regression_acceptable`: did the candidate introduce an unacceptable
  visible regression? This is a quality decision and is required for Phase4.
- `change_visibility_sufficient`: was the candidate delta large enough to judge
  the intended correction at normal viewing scale? This is a diagnostic field.

An answer such as “the difference is too small to see” is **not** equivalent to
“the result is visually unacceptable.” It sets
`change_visibility_sufficient=false` and requires a magnified/cropped review or
an explicit follow-up, while leaving `visual_regression_acceptable` unanswered.
It must not be silently converted into either a Phase4 PASS or a quality FAIL.

The verifier can return `Phase4: PASS` only. Its output always remains
`Phase5: NO_GO`, `Golden: HOLD`, and `production: NO_GO`; later promotion is a
separate gate.
