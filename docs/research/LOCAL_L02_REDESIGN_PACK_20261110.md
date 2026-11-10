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

