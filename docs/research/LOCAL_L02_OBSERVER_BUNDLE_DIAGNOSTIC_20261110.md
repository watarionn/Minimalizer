# L02 observer bundle診断: 接触成分の役割衝突

更新日: 2026-11-10

## 目的

数画素のowner修正をやめ、署名済み原画像だけから複数observerの証拠を束ねる
component graphを実画像で確認した。これは推論後の診断であり、人手maskや既存ownerを
入力にしていない。owner番号、Phase4候補、production出力は生成していない。

実装は `tools/research/local_l02_observer_component_graph.py`。Sapiens2、SCHP ATR18、
SCHP LIP20の出力を、`garment`、`upper_clothing`、`outerwear`、`arm`の役割付き
observerとして渡し、8連結unionをcomponent単位で調べた。

## 実画像での結果

| case | observer観測 | unknown | union components | role conflict | role evidence |
|---|---:|---:|---:|---:|---:|
| H06 | 550,441px | 52,428px | 42 | 3 | 39 |
| H08 | 430,855px | 106,004px | 33 | 1 | 32 |

H06の最大衝突componentは534,538px、H08の最大衝突componentは422,174pxで、両方
とも腕・衣装・上衣・外衣が接触した人物本体の大成分だった。これは単純ORで採用
すべきという意味ではない。逆に、全unionを一つのcomponentとして扱うだけでは、
衣装全体をunknownにしてしまい、正衣装保護と腕の誤owner除去を同時に解けない。

## observer単体の診断値

以下は凍結後の人手評価にのみ使った診断値であり、推論や閾値選択には使っていない。
`unknown` はラベル未観測領域で、陰性ではない。

| case / observer | predicted | known-positive hit | known-negative FP | unknown | arm overlap | underlayer overlap |
|---|---:|---:|---:|---:|---:|---:|
| H06 ATR upper | 315,765 | 280,005 | 2,616 | 33,144 | 733 | 1,883 |
| H06 LIP coat | 85,206 | 82,963 | 0 | 2,243 | 0 | 0 |
| H06 ATR∩LIP | 84,681 | 82,621 | 0 | 2,060 | 0 | 0 |
| H08 ATR upper | 206,338 | 139,764 | 678 | 65,896 | 678 | 0 |
| H08 LIP coat | 228,022 | 154,818 | 5,906 | 67,298 | 5,906 | 0 |
| H08 ATR∩LIP | 192,555 | 139,283 | 678 | 52,594 | 678 | 0 |

H06ではLIP coatの意味精度は高いが再現が低く、H08ではLIP coatの再現は高いが腕の
混入が残る。単純なobserver OR/ANDやケース別閾値では、正衣装と腕の意味を両例で
同時に満たせない。

## 判定

この結果は「小さな修正を追加すべき」という意味ではない。次の根本欠落を示す。

1. observerの役割ごとの証拠を、union前に保持する必要がある。
2. 役割が接触する大成分を、外形だけでなく接触境界と遮蔽順序で分解する必要がある。
3. observer間の一致はowner権限ではないため、境界の根拠が足りない部分は部分的な
   pixel patchではなく、意味region全体をunknownにする必要がある。

## 次の大きな実装単位

`contact-aware role graph`を作る。

- 各observerのrole maskとsource alphaを独立に保持する。
- union全体の巨大componentをそのままowner化しない。
- role間の接触、包囲、穴、4/8連結、source境界をグラフの辺として記録する。
- 独立observerが同じrole境界を示す部分だけを候補regionにする。
- 境界が腕・袖・下着・遮蔽のどれか決められないregionは、region全体をunknownにする。
- H04/H06/H08を同じ実装で一括実行し、case別閾値は持たない。

この層ができるまで、既存ownerへの追加削除、Phase4 receiptの昇格、Phase5、L04、
Golden、本番変更は行わない。現状は `L02=HOLD / Phase4=FAIL / Phase5=NO_GO` を維持する。
