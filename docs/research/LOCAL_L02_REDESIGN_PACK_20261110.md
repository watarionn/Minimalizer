# L02再設計パック: 意味ownerを一括再構成するための開発契約

更新日: 2026-11-10

## 目的

H06/H08の数画素修正を続けず、H04/H06/H08の全身画像で同じ意味owner契約を成立させる。
この文書は新しい候補の品質合格を宣言するものではない。次の大きな実装サイクルに入る
ための設計契約であり、ここが埋まらない限り候補生成を始めない。

## 現行候補から確定した問題の大きさ

| ケース | 現行候補の診断 | 根本的に解くべき境界 |
|---|---|---|
| H04 | known-only IoU `0.915065`、known FP `3,459`、FN `1,300` | 正衣装と手・腕の境界、blazer全体のowner一貫性 |
| H06 | known-only IoU `0.887601`、known FP `15,394`、FN `21,722` | 外衣・袖・腕・白い下着／カフの分離、遮蔽順序 |
| H08 | known-only IoU `0.955548`、known FP `183`、FN `6,785` | 袖・肩の回復と腕の排他的owner、ポーズによる遮蔽 |

これは共通の数画素ノイズではない。衣装のまとまり、身体部位との接触、下着の可視性、
遮蔽の前後関係を画像全体で再構成できていないという意味である。

## 既に棄却した設計

### 汎用人体パーサーの単純arm-veto

FASHNの `top` はH06で衣装全体を覆い、腕クラスは検出されなかった。H08でも腕観測が
ほとんどなく、腕unionを一律に引くと正しい袖の回復まで失う。ATR/LIP/FASHNの腕union、
袖診断maskで保護する変種も、H06とH08を同時には満たさない。

したがって、次の処理は採用しない。

- 全身衣装maskから腕maskを一律に引く
- 腕observerの一致だけで衣装ownerを剥がす
- classやthresholdをケース別に変える
- 既存ownerを正解として残差だけを修正する

## 次の大きな実装の責務

次の候補生成器は、少なくとも次の4層を一つの凍結出力へ束ねる。

```text
signed source
   │
   ├─ garment proposal: 外衣・袖・下着の候補領域
   ├─ body/limb evidence: 腕・手・脚・顔の候補領域
   ├─ occlusion relation: 前後関係と接触境界
   └─ source geometry: alpha・連結成分・穴・境界
              │
              ▼
       component-level owner solver
       ├─ 排他的owner
       ├─ unknown / abstain
       └─ conflictを成分全体で保留
```

この責務の最初のsource-free実装を
`tools/research/local_l02_component_owner_solver.py` に追加した。現段階では、
候補instanceが腕／下着observerと衝突する接触component、または複数instanceが
重なる接触componentを、部分削除せずcomponent全体unknownへ戻す。衝突のない単一
instanceだけを新しいowner番号へ割り当てる。これは設計の骨格を検証する研究層であり、
まだH04/H06/H08の実画像候補、Phase4、owner authorityを意味しない。

次の大きな実装では、signed sourceから得た実observer出力をこのAPIへ束ね、三例を
同じ契約で一括処理する。既存owner配列をこの層へ渡す引数は設けない。

最初の実画像probeでは、arm evidenceだけで接触componentを判定したため、H06/H08の
正衣装領域を大量にunknownへ退避し、H06 IoU `0.327063`、H08 IoU `0.000224`となった。
この結果はsolverの部分修正を促すものではない。underlayerと遮蔽順序を観測する層が
不足していることを示すため、次の実装単位はその意味観測を追加した一括再構成である。
観測層を用意できない場合、Aは候補を作らず `HOLD` を維持する。

Fashionpediaの固定base-layerクラスを同じsolverへ追加する派生も試したが、H04/H06/H08
とも三例共通の品質を満たさなかった。この派生は正式経路から除外し、次に必要なのは
同一モデルのクラス足しではなく、外衣・下着・腕・遮蔽順序を別々に観測できる独立層である。

重要なのは、observerを増やすことではなく、observerの不一致を意味ownerへ変換する
規則を根本から作ることである。意味を決められない領域は、既存ownerの都合で埋めず、
成分全体をunknownとして凍結する。

## 実装開始前に埋める設計項目

次の項目がsource-free資料と小さな構造テストで説明できるまで、候補を生成しない。

1. garment / sleeve / arm / underlayer / occlusion の各入力信号と、信号が欠けた場合の扱い。
2. 同一component内で意味が衝突したときの分割条件と、分割できない場合のunknown化。
3. H04/H06/H08の各境界を同じ規則で扱えること。画像別分岐は禁止。
4. 推論入力に人手mask、既存owner、レビューJSON、既知ラベルを含めないこと。
5. 出力が排他的owner、unknown、source alpha、4/8連結、穴、接触関係を同時に満たすこと。
6. 通常倍率で全体差分が認識でき、意味クラス別の拡大表示で変更理由が追えること。
7. 一括評価で一例でも意味境界を壊した場合、候補を正式経路から破棄すること。

## サイクルの成果物

一つのサイクルで作ってよい候補は一つだけ。H04/H06/H08を同じコード・同じ設定で処理し、
次をまとめて保存する。

- source-onlyの実行receiptとobserverのrevision／重み／出力SHA
- 全身owner map、unknown map、遮蔽関係、component構造結果
- 通常倍率の全体before/afterと意味クラス別拡大表示
- 失敗クラス別のPASS / FAIL / UNKNOWN表
- 採用候補のfreeze SHA、または正式経路から破棄した記録

候補がFAILした場合、次に変えるのは原因モデルまたは観測設計であり、同じ候補の画素・
threshold・owner配列ではない。

## 完成へ進める条件

この再設計サイクルを通過し、H04/H06/H08すべてで独立Phase4がPASSした後だけ、
Phase5 exact replay、L04三点セット、L05/L07、Golden、本番、実機iPhoneへ進む。
現時点のA/B状態は変わらず、`L02=HOLD / Phase4=FAIL / Phase5=NO_GO` である。

## 2026-11-10 layered solver probeの判定

外衣proposal、Sapiens2の腕観測、接触・遮蔽規則を組み合わせたsource-only probeを
H04/H06/H08へ同じコード・同じ設定で実行した。人手mask、review JSON、凍結ownerは
推論入力に使用していない。推論後の比較だけで確認した結果、変更はH04 148px、H06
1,926px、H08 170pxであり、H06はIoUが`0.887601`から`0.885709`へ悪化した。

これは「全身owner再構成」ではなく、既存Fashionpedia外衣proposalの周辺差分である。
よってこのprobeは`MICRO_DELTA_ONLY`または`REGRESSION`として研究履歴へ隔離し、
正式候補、Phase4、owner認可、L04 handoffには使用しない。

この失敗に対する次の行動は、solverの追加修正ではない。外衣・袖・腕・下着・遮蔽関係・
人物内instance結合を同時に観測できる実行可能observerを、モデル／重みSHA／出力契約
まで含めて先に確定する。能力ゲートを通過できない限り、Aの候補生成を停止する。

