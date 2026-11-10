# L02 独立レビュー差分 readback（2026-11-10）

この文書は、非公開Driveに追加された最新レビューの差分だけを記録する
source-free台帳である。原画像、マスク、NPZ、比較画像は保存しない。

## 受領した証拠

- Drive file: `H04_H06_H08_Sapiens2_独立visual_review_signed_20261110.txt`
- Drive ID: `1DrpR2bYIdDi-KPcyTqkzAm39g30qN3Ni`
- URL: https://drive.google.com/file/d/1DrpR2bYIdDi-KPcyTqkzAm39g30qN3Ni/view?usp=drivesdk
- downloaded size: `1122` bytes
- downloaded SHA-256: `8e83eabc93f1e6beb559beb713d79a49ac9bb280ec5ab772397d7af969f4950c`
- reviewer: `Tento`
- evaluated: `2026-11-10 07:47 JST`
- response signature: `てんと`

回答本文から、評価者は開発側ではなく、推論前にラベルまたは過去予測を見ていないと
読み取れる。評価対象の意味評価（正衣装保持、誤owner除去、腕・下着・遮蔽・重要部位）も
H04/H06/H08について肯定されている。

## 「いいえ」の正しい意味

原レビューでは、品質の悪化と変更量の視認性が一つの質問に混在していた。H06/H08の
`visual acceptable = いいえ` は、評価者の補足「何が違うのか人間には全くわからない」と、
別途受領した clarification の意味に従い、次のように分解する。

| case | 候補SHA | 変更画素 | bbox | 差分の意味 |
|---|---|---:|---|---|
| H04 | `5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e` | 0 | - | 変更なし。改善証拠ではない |
| H06 | `87278640b0761e6d3aa572cb37156f13ee09bc8c9ebaef133445ffec63bbfa76` | 4 | `(1237,1090,1307,1150)` | 通常倍率では変更箇所が小さすぎて判定困難 |
| H08 | `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091` | 591 | `(799,639,1163,724)` | 通常倍率では変更箇所が小さすぎて判定困難 |

したがって、この回答を「H06/H08の画像が悪い」「修正が失敗した」とは扱わない。一方で、
差分を視認できる十分な変更であることも証明されていない。`visual_regression_acceptable`
と`change_visibility_sufficient`は別フィールドで受領しなければならない。

## 現行ゲート

- 独立性・未見性・推論前ラベル非参照: `YES`（受領レビューの主張）
- 意味評価: `YES`（受領レビューの主張）
- H06/H08の差分視認性: `未完了`
- H04の候補改善: `未成立`（変更画素0）
- 現行L02/Phase4: `HOLD / FAIL`
- Phase5、owner認可、Stage8、Golden、本番: `NO_GO`

このレビューはSapiens2の小差分候補に対する評価であり、六能力observerの成立証拠でも、
現在設計中の全身owner再構成候補のPhase4 PASSでもない。したがって、現在のA候補を昇格せず、
「通常倍率で判定できる大きさの三例一括候補を一つ作る」という開発方式を維持する。

## 次の実作業

1. H06/H08について、private review boardで差分領域を拡大表示する。
2. 評価者へ、悪化の有無と意図した修復の視認性を分けた二問を渡す。
3. 回答を署名付きreceiptへ固定する。
4. 三例一括で視認可能な意味改善がない場合、同じ候補を数画素単位で繰り返さず、
   observer能力ゲート／全身owner再構成へ戻す。
