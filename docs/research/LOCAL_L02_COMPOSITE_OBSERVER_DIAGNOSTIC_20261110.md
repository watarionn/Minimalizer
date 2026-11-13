# L02 composite observer 三例診断

更新日: 2026-11-10

## 目的と境界

See-throughのlayer出力、Fashionpediaの外衣・袖検出、Sapiens2の腕検出を、固定された
source-only写像で三例へ一括照合した診断である。人手mask、レビューJSON、既存ownerは
推論入力に使っていない。これは候補生成・Phase4・owner認可ではなく、観測不足の原因を
特定するための研究記録である。

Fashionpediaは固定ontologyの外衣 `{cardigan, jacket, vest, coat, cape}` と `sleeve`、
Sapiens2は固定arm class集合、See-throughは既存の`topwear`/`handwear`を使った。
画像別の閾値、座標、OR/AND、レビュー結果による後合わせは行っていない。

## 診断値

| case | source alpha | outerwear | sleeve | arm raw | arm exclusive | broad topwear | derived residual | topwear/handwear overlap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| H04 | 72,671 | 16,646 | 4,594 | 4,040 | 4,025 | 20,143 | 6,752 | 3,713 |
| H06 | 88,859 | 46,660 | 10,660 | 695 | 244 | 64,972 | 27,960 | 8,756 |
| H08 | 79,153 | 22,569 | 12,158 | 1,521 | 1,517 | 32,334 | 17,227 | 7,180 |

`derived residual`は`topwear - outerwear - sleeve - arm`で作った残差であり、独立した
underlayer observerではない。残差が非空でも、内側衣装の意味ownerや正衣装保持を証明しない。

## 不足の確認

- `outerwear`、`sleeve`、`arm`は候補領域を出せるが、外衣と袖の重複はH04 `4,551`、
  H06 `10,379`、H08 `12,129`画素あり、排他的ownerの根拠にならない。
- `underlayer`は全例で広い`topwear`の残差としてしか得られず、独立観測ではない。
- LayerDiffのdepth比較から非ゼロ値が出るのは`topwear`対`handwear`の重複だけで、必須の
  外衣/下層・袖/腕・衣装/身体の3 pairを満たさない。
- source foregroundの8連結成分数はH04 `1`、H06 `12`、H08 `1`であり、これは人物の
  source geometryであってgarment instance groupingではない。

## 判定

```text
六能力observer: HOLD
候補昇格: 不可
Phase4: FAIL
```

この診断から、残差の改名、連結成分のinstance化、depth一枚の遮蔽代用、重複部分の
閾値・形態学処理を追加しない。次の正式入力は、
`LOCAL_L02_OBSERVER_ADOPTION_PLAN_20261110.md`のpairwise relationとinstance契約を
満たす実行可能checkpoint、または同契約で学習したobserverだけとする。

## 保存

原画像、mask、NPZ、座標、比較画像は非公開Drive側に保持し、このsource-free記録には
診断値と判定だけを保存する。現行候補、Phase4 receipt、Stage8三点セット、Golden、
productionへは接続しない。
