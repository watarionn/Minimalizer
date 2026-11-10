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

## 人間がreceiptを作る手順

人間はJSONを直接書かない。現行の凍結候補から、source-freeの記入用テキストを作る。

```cmd
py -3 tools/research/prepare_local_l02_phase4_receipt.py init ^
  --freeze C:\path\to\SAPIENS2_CANDIDATE_FREEZE_RECEIPT.json ^
  --output C:\path\to\PHASE4_REVIEW_FORM_CURRENT.txt
```

記入者はフォームの空欄だけを埋める。特に、`visual_regression_acceptable`（悪化がないか）と
`change_visibility_sufficient`（意図した修復を通常倍率で判定できるか）は別々に回答する。
差分が小さくて判定できない場合、後者を`NO`にし、前者を勝手に`YES`へ補完しない。

記入後、現行freeze receiptとフォームを渡してJSON化する。

```cmd
py -3 tools/research/prepare_local_l02_phase4_receipt.py materialize ^
  --freeze C:\path\to\SAPIENS2_CANDIDATE_FREEZE_RECEIPT.json ^
  --form C:\path\to\PHASE4_REVIEW_FORM_CURRENT.txt ^
  --output C:\path\to\PHASE4_INDEPENDENT_REVIEW.json
```

未回答、旧候補SHA、署名・時刻不足、三例のどれか一つでも不成立なら、JSONは生成されず
`HOLD`になる。生成されたJSONもPhase5、Golden、本番を自動承認しない。
