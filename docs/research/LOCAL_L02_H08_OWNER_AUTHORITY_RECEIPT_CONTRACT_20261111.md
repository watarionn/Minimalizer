# H08 owner-authority receipt contract

このreceiptは、H08のowner遷移だけを、現行の署名済み元画像・凍結owner・候補owner・
observer出力へ結び付ける。画像、マスク、NPZ、評価ラベルは読み込まず、Golden、
本番、mergeを認可しない。

現行の固定値は次のとおり。

| 対象 | SHA-256 |
|---|---|
| 署名済みH08元画像 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` |
| 凍結owner | `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52` |
| 現行候補owner | `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091` |
| observer出力 | `e3d54bea29d1569e16b2aa18e4a6bd34c37d76530449c73114e5511b3b3e4423` |

準備器は`tools/research/prepare_local_l02_h08_owner_authority_receipt.py`。
`init`で人間向けフォームを作り、`materialize`で全SHA結合、owner遷移の明示承認、
unknown非昇格、人手ラベル非入力、production未認可を確認したときだけJSONを出力する。
古い候補SHA、未回答、別caseの値ではHOLDになる。

今回のprivate kitでは、ワタルの明示承認を上記H08候補へ結び付けたreceiptを作成済み。
このreceiptはowner認可の記録であり、Phase5の構造PASSやGolden・本番PASSではない。
