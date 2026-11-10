# H08 owner-authority receipt（2026-11-09）

Status: **対象固定済み / Phase4 は未判定 / promotion は未認可**

## 認可内容

所有者は、H08 の owner-authority receipt が参照する frozen owner map を、次の SHA-256 に固定することを認可した。

`43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52`

この認可は、H08 の後続 Phase4 評価で入力来歴を取り違えないための対象固定である。owner promotion、Phase4 PASS、Phase5 昇格、Golden、production、LocalWorker 反映を認可するものではない。

## 固定された対象

| 項目 | 値 |
| --- | --- |
| case | H08 |
| signed source SHA-256 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` |
| frozen class-id array SHA-256 | `d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5` |
| frozen owner array SHA-256 | `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52` |
| independent observer array SHA-256 | `3dd9b6e01d2584247543abbe64f543e1ec1d0d55ab6231d3d7d2783a2d0cbcfa` |
| source-only rule | human mask/review JSON は推論入力に使わない。unknown を陰性にしない。 |
| known historical replay | source-only positive 8,371px のうち 591px を候補割当したが、これは historical candidate であり採用出力ではない。 |

## 明示的な除外

- SegFormer の新規 H08 clothing prediction `8e3613bf90202a5a04a58f53b7ba66e755a601494e37fac1a5137ad06bcf4275` は owner map ではないため、本receiptの対象外とする。
- private 評価 package 中の `H08_OWNER_4_PRIVATE.npz` SHA `0a352e424c993deac3494c1b9fbf8716fb4cfd7fe78fa688f197eadc0c3607be` は producer/config と Phase4 candidate の来歴結合が未整備のため、本receiptの対象外とする。
- license evidence はこのreceiptおよびL02のgateではない。

## 次の必須作業

1. materialized candidate とprivate receiptは [H08 Phase4 materialized receipt](../research/LOCAL_L02_H08_PHASE4_MATERIALIZED_RECEIPT_20261109.md) に記録済みで、結果は FAIL である。
2. H08の残存誤ownerと衣装FNの最初の失敗点を分離する。固定済み対象を別owner mapへ差替えない。
3. Phase4 が独立PASSするまで、Phase5、Golden、productionへ昇格しない。

## 認可根拠

所有者の明示指示（2026-11-09）: ``43d164… をH08 receiptの対象として固定してよい``。
