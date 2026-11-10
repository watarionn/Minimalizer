# MinimalizerLocal 開発方式の再設計と完成工程

更新日: 2026-11-10

## 目的

H06/H08の数画素を何度も足し引きする開発を終了し、完成に必要な根本問題を、
まとまった設計単位で解決する。過去の候補・observer・receiptは履歴として保存するが、
新しい候補の入力や完成の根拠には戻さない。

この文書は、Aの画像品質とBの表示・配信を混同せず、それでも完成までの道筋を一つに
追跡するためのキャンペーン工程表である。

## 開発結果の定義を変える

一回の作業で「少し良くなった」を成果として扱わない。正式な成果は次の三つだけとする。

1. 根本設計をsource-free資料と構造テストで通過した。
2. H04/H06/H08を同一契約で処理した全身候補が、意味評価を含む一括ゲートに通過した。
3. 根本原因が解けず、候補を正式経路から棄却し、次に変える設計前提を記録した。

次は成果として数えない。

- 数画素の追加・除去
- ケース別の閾値変更
- observerを一つ増やしただけの出力
- receiptやレビュー用紙を候補不足の穴埋めに使うこと
- metricsだけが改善し、通常倍率で意味の変更が確認できないこと

## 完成までの大工程

```text
R0 基準整理・台帳統合
  ├─ signed source / SHA / local / GitHub headを固定
  ├─ baseline / diagnostic / supersededを分類
  └─ 過去データを正式入力から隔離
          │
          ▼
A1 根本品質設計
  ├─ garment / sleeve / arm / underlayer / occlusionを同時に観測
  ├─ component単位でownerまたはunknownを決定
  ├─ H04/H06/H08共通規則を構造テストで検証
  └─ ここを通るまで実画像候補を作らない
          │
          ▼
A2 全身候補と独立Phase4
  ├─ 三例を同一実装・同一設定で一括推論
  ├─ 構造検査、意味評価、通常倍率の視覚レビュー
  └─ PASSした一つのfreeze SHAだけを正式採用
          │  FAILなら候補を破棄し、A1へ戻る
          ▼
B1 正式引き渡し・L04/L05/L07
  ├─ Aのfreeze SHAをexact handoff
  ├─ 元画像 / Stage8 JSON / 展開SVGを三点照合
  ├─ private HTTPS、PC、Safari/PWA、offline復帰、障害系
  └─ generation-pinned SWと実入出力を検証
          │
          ▼
R1 Golden・本番・実機受入
  ├─ Golden承認
  ├─ 本番反映とrollback/readback
  └─ 本番後のiPhone受入
```

## R0: 基準整理・台帳統合

### やること

- 署名済みH04/H06/H08元画像とsource SHAを正本として固定する。
- AとBのローカルhead、GitHub head、PR headを同じ時点で読み戻す。
- すべての既存成果を `baseline`、`diagnostic`、`superseded` に分類する。
- 旧候補を新しい推論入力から除外し、比較専用にする。
- raw画像、NPZ、mask、座標、比較画像は非公開Driveに置き、GitHubには入れない。

### 完了条件

台帳だけを読めば、現行正式候補、参考候補、棄却候補、未解決ゲートを区別できること。
ここで品質候補を作らない。

## A1: 根本品質設計

Aの未解決問題は「どの画素を数個動かすか」ではない。衣装全体の意味ownerを、
腕・袖・下着・遮蔽との関係を含めて再構成できていないことである。

### 必須の設計

- signed sourceから得るgarment proposal
- body/limb evidence
- underlayer evidence
- occlusion relation
- source alpha、4/8連結、穴、接触component
- 衝突時のcomponent全体unknown化
- unknownを陰性に変換しない排他的owner規則

既存owner、人手mask、レビューJSON、既知ラベルを推論入力に使わない。設計がこの条件を
満たせない場合、追加の小修正をせずAをHOLDのままにする。

### モデル選定の大きさを先に判定する

次の大規模サイクルで、単にsemantic maskをもう一つ足すことはしない。候補となる
source-only観測構成（単一モデルまたは役割を固定した少数のモデル群）は、実装前に
次の能力を一括で持つかを確認する。

- garment / sleeve / arm / underlayerを同時に出せること
- 同一人物の各部位を同じinstanceへ結び付けられること
- 可視領域と遮蔽・接触境界を区別できること
- H04/H06/H08へ同じ推論契約で実行できること
- revision、重みSHA、出力SHAを凍結できること

単一のsemantic parsingモデルは、衣服や腕のクラスを返せても、衣装のinstance帰属や
遮蔽順序を保証しない。この不足をsolverの数画素補正で埋めない。各観測層のコード・
重み・出力契約が揃い、組み合わせ後のunknown規則まで再現できなければ、A1は
「観測層不足」としてHOLDにする。

公開研究には、衣服・身体部位のpixel parsingとinstance-level groupingを一つのネット
ワークで扱う設計がある。しかし、プロジェクトページ上で実行用コード・重みが確認できる
までは、Minimalizerの候補として採用しない。また、multi-human parsingの公開実装は
衣服カテゴリと人物identityを扱えるが、実行可能なcheckpointとH04/H06/H08への適用条件を
先に確認する。つまり、モデル名や論文の存在を成果にせず、三例一括の再現可能な実行が
確認できたものだけをA1の設計候補とする。

### A1の中止条件

- H04/H06/H08で同じ規則を使えない
- 腕観測だけで正衣装まで削る
- 下着・遮蔽を観測できないままownerを決める
- unknownを既存ownerで埋める
- 通常倍率で確認できるまとまった変更を作れない

## A2: 全身候補とPhase4

A1を通った後に限り、三例を一つの実行で処理する。ケース別後合わせは禁止する。

一つの候補に次を束ねる。

- source SHA、observer model/revision/weight SHA/output SHA
- 排他的owner map、unknown map、遮蔽関係
- 4/8連結、穴、alpha、componentの構造結果
- 正衣装保持、腕・袖・下着の誤owner除去、遮蔽順序の意味評価
- 通常倍率の全体表示と、意味境界の拡大表示
- freeze SHAと推論後レビューのreceipt

三例のうち一例でも根本境界を壊したら、候補は正式経路から破棄する。同じ候補へ
画素修正を重ねない。

## B1: Aとは別の完了条件

Bは画像品質を直す担当ではない。Aが渡したfreeze SHAを、正確に表示し、安全に配信し、
障害から復旧できることを確認する担当である。

したがって、A2 Phase4がPASSするまではBへ正式handoffしない。ただしBの既存コードに
対する読取QA・テスト・差分整理は独立して進めてよい。

B1の成果は次に限定する。

- L04: 元画像、Stage8 JSON、展開SVG、manifestの三点照合
- L05: 実際の入力・出力、429/Retry-After、失敗系、競合、private HTTPS
- L07: generation-pinned Service Worker、cache境界、offline復帰、Safari/PWA
- 本番反映前後のreadbackとrollback証拠

BのPASSはAのPhase4 FAILを上書きしない。Aの画像品質をB側で補正しない。

## 変更の大きさの基準

「変更結果を視覚的に受け入れられる」は、変更が小さすぎて意味を評価できない場合も
含む。この場合は「画像が悪い」と断定するのではなく、正式候補として不成立とする。

次の候補は、腕・袖・下着・遮蔽などの失敗クラス全体を含む、通常倍率で識別可能な
まとまった再構成でなければならない。小さい差分を積み上げて視覚レビューを通すことは
しない。

## 現在の判定と次の一手

```text
A L02          HOLD
Phase4         FAIL
Phase5         NO_GO
B L04          A正式handoff待ち
B L05/L07      既存QAは保持、production反映は未完了
Golden         HOLD
production     NO_GO
```

次に実施するのは、現行候補への追加修正ではない。A1の設計パックを、外衣・下着・腕・
遮蔽順序を同時に観測できる実行可能な構成として確定し、その構成でH04/H06/H08を
一括処理できるかを検証する。構成が成立しなければ、候補生成を増やさず、具体的な
観測不足を記録してAをHOLDする。

## 公開仕様の確認先

2026-11-10時点の設計調査で参照した公開ページ。ここで確認したのは能力の候補であり、
Minimalizerへの採用・品質合格・owner権限を意味しない。

- [Spectrum project](https://s-pectrum.github.io/): clothing/body-part parsingとinstance-level groupingを掲げる研究仕様。
- [Multi-Human-Parsing](https://github.com/ZhaoJ9014/Multi-Human-Parsing): semantic partと人物identityを同時に扱う公開実装・データ仕様。
- [FASHN Human Parser](https://huggingface.co/fashn-ai/fashn-human-parser): 18クラスのsemantic parsing仕様。instance帰属・遮蔽順序の根拠としては不十分。

追加確認として、[clothes-segmentation](https://github.com/mxrxm/clothes-segmentation) は
instance単位の衣服maskと23カテゴリ、実行用checkpointを公開している。一方で同資料自身が
遮蔽衣服の不完全検出を制限として挙げているため、これは「garment proposal層」の候補で
あって、腕・下着・遮蔽順序を解決する完成モデルではない。まずこのように役割を分けて
能力不足を明示し、組み合わせ全体をH04/H06/H08で一括評価する。単独の見栄えや論文上の
性能を理由に採用しない。

同じ確認で、[Multi-Human-Parsingの公開実装](https://github.com/ZhaoJ9014/Multi-Human-Parsing)
はinstance/partの学習コードと評価コードを含むが、公開READMEの実行手順は学習と
ImageNet事前学習重みの準備を前提としており、今回の三例に直ちに再現できる完成checkpoint
としては扱わない。これは不採用の品質判定ではなく、実行可能性ゲート未通過という意味で
履歴へ残す。

