# MinimalizerLocal 統合キャンペーン現況・保存方針

更新日: 2026-11-10

この文書は、Lane A（実画像品質）とLane B（L04/L05/L07統合）の現在地を
一枚に固定するための source-free 台帳である。過去の実験結果を削除したり、
正式ゲートを自動昇格したりするものではない。

## 正本と現在の作業点

| 対象 | SHA / 状態 |
|---|---|
| 最新 `origin/main` | `616d832e8223ba40dbf1030afd0bbc83f6f5b5df` |
| Lane A PR #449 | Draft / `research/local-l02-class32-topology-palette-shadow-20261102` / current head `18932952fcf8568e9d60a71719c8d071964d3a7e` |
| Lane B PR #451 | mainへ統合済み（squash後の統合先は上記main SHA）。Aの品質候補をBへ混ぜない |
| A L02 / Phase4 | `HOLD` / `FAIL`（キャンペーン正式昇格なし） |
| Phase5 | `NO_GO`（Phase4独立PASS前は禁止） |
| L04 handoff | `false` |
| Golden / production | `HOLD` / `NO_GO` |

### 2026-11-10 最新readback

上表とこの節が現在の判断であり、下に続く過去の記録は履歴として保持する。

- Lane Aで `local_l02_observer_evidence_contract.py` と対応テストを追加した。
  source-alpha、source-only、unknown保持、human label／既存owner不使用、役割重複、
  mask SHA／shape、遮蔽関係、instance groupingを検証し、欠落時はownerを生成せず
  `CAPABILITY_HOLD`で停止する。
- Aの `test_local_l02_*.py` 全体は、依存済み隔離venvと`tools/research`を含む明示的な
  import pathで再実行し、`472 passed`。これは構造・契約テストのPASSであり、画像品質や
  Phase4 PASSではない。
- Bの統合回帰（L04三点、L05 receipt、L07監査、Worker、handoff）は `67 passed`。
  Bの実装・source/runtime QAは完了状態を維持し、Aの品質判定は行わない。
- 現行See-through出力は、外衣・下着・袖・腕・遮蔽関係・人物内instance groupingを
  同時に満たすobserver evidence bundleになっておらず、候補側にもsource-alpha外の
  mask画素が確認されたため、正式入力として不採用。`L02=HOLD / Phase4=FAIL /
  Phase5=NO_GO / Golden=HOLD / production=NO_GO`を維持する。
- 追加の実行checkpointとして、ローカルのSee-through SAM-HQ 19部位モデルを署名済み
  H04/H06/H08へ同一条件でsource-only実行した。source alpha内へclipした後も、三例
  共通で観測できたのは`outerwear`相当と`sleeve`相当だけで、`arm/underlayer/
  occlusion_relation/instance_grouping`が欠落し、全例`CAPABILITY_HOLD`だった。
  `topwear`の改名、`handwear`の腕流用、depth・連結成分の遮蔽代用は採用しない。
- 次のA工程は、同じ署名済みH04/H06/H08へ一括適用できる六能力observer、または
  その能力を導入・学習する実行可能な計画を確定すること。計画の正本は
  `docs/research/LOCAL_L02_OBSERVER_ADOPTION_PLAN_20261110.md`である。能力契約を満たすまで、
  閾値、OR/AND、case別選択、数画素修正、Phase4 receiptの追加は行わない。
- 公開候補の追加監査では、Spectrumは能力説明は有望だが実行可能checkpointを確認できず、
  FASHN/Sapiens2/衣服instance segmentationも六能力を同時に満たさなかった。詳細は
  `docs/research/LOCAL_L02_CHECKPOINT_AVAILABILITY_AUDIT_20261110.md`に固定した。
- ルートIIの最初の実装として、訓練manifest検証器とテストを追加した。H04/H06/H08の
  holdout混入、人物単位のsplit漏洩、unknownの陰性化をfail-closedにするが、学習データや
  observer checkpoint自体はまだ生成しない。
- 全体トップレベル回帰は `1565 passed / 13 failed / 46 subtests passed`。FAILは
  今回のA/B変更ではなく、旧Browser v11/v12期待値、既存missing fixture、Torchの
  import順、現行Web実装と旧テストの不整合であり、別修復対象として分離する。

2026-11-10の方式再設計として、Aのobserver能力ゲートをコミット
`51a68bc0e06e7c12842eac6d84f1fc71dae318e5`へ固定し、PR #449のDraft headへ反映した。
`tests/test_local_l02_observer_capability_gate.py`を含む対象テストは`15 passed`。
この変更は候補画像を作らず、現行See-through body-part parserを
`CAPABILITY_HOLD`（外衣・下着・袖・腕・遮蔽関係・instance grouping不足）として
候補生成前に停止する。したがって、A/Bの品質状態は上表から昇格していない。

2026-11-10の読み取り専用B再検証では、PR #451 head
`c593b46c53c28127b08d74d2ce733045495b5577` に対してL04/L05/L07/Workerの
focused suiteが `46 passed`。Service Worker generation pin、shell-only cache、
no-store route、offline shell fallback、L05 concurrency契約を静的に確認した。
これはBのsource/runtime QAであり、production反映・実機iPhone受入・L04正式三点
セットの完成を意味しない。L07監査自身も `L07_actual_live_iphone=NOT_TESTED`、
`L08_release=NOT_APPROVED` を返している。

## AとBの役割

```text
署名済み元画像
      │
      ▼
A: source-only推論 → owner/腕/下着/遮蔽の意味評価 → Phase4
      │                         │
      │ Phase4 PASS のみ         └─ FAIL/HOLDなら候補を凍結して停止
      ▼
Phase5 exact replay
      │
      ▼
B: Stage8三点照合 → SVG/Chromium/予算 → PWA/Worker/障害系
      │
      ▼
Golden承認 → 本番反映 → 実機iPhone受入
```

BはAの画像品質を判定する担当ではなく、Aが正式に渡した結果を壊さず表示・
配信・復旧できるかを確認する担当である。したがって、Bが機能的にPASSでも、
AのPhase4がFAILなら完成にはならない。

## 保持するもの

次のものは、後からSHA・来歴・再現条件を確認するため必ず保持する。

- 署名済みH04/H06/H08元画像のSHA対応表と、候補出力のfreeze receipt。
- source-only推論コード、observerのモデル／重み／class-map／出力SHA、負例テスト。
- Phase4独立評価receipt、候補SHA、source SHA、評価者・時刻・署名の結び付き。
- H04/H06/H08それぞれのPhase4、Phase5、Stage8、L04三点セットのsource-free台帳。
- L04の元画像・Stage8 JSON・展開SVG・manifest・gate resultの相互SHA。
- L05/L07の実際のHTTP、429/Retry-After、fallback、offline復帰、PC/iPhone記録。
- PR、コミットSHA、テスト結果、HOLD/FAIL/NO_GOの理由。

原画像、マスク、NPZ、座標、比較画像はGitHubへ入れず、承認済み非公開Driveに
保持し、既存のreadback記録とSHAを残す。

## 参照のみとして隔離するもの

古いRun、候補NPZ、既知例への後合わせ、label付きpost-score、旧Stage8、旧SVG、
旧cap試行は削除せず、`historical / superseded / not-formal` として保管する。
これらを新しい候補の推論入力や正式品質証拠には戻さない。

特に次は正式対象外である。

- 現在のH08 `H08_PHASE4_MATERIALIZED_RECEIPT.json`（`phase4=FAIL`）。
- `formal-triple-preserving-package-v2`（H04一式がなく、H06/H08のmanifestも不足）。
- `1887` capで作られた、正式方針の確認がない旧L04候補。
- 独立評価結果の意味を示す資料であっても、現在の候補SHAと署名を結ばないJSON。

## 次に実行する工程

具体的な順序と、局所修正を再開しない条件は
`docs/research/LOCAL_L02_DEVELOPMENT_METHOD_RESET_20261110.md`を正本とする。
現時点の次作業は、旧候補を正式入力から隔離したうえで、H04/H06/H08の意味クラス別
失敗表を一枚に固定し、三例同時の全身outerwear候補を独立レビューへ渡すことである。
候補フォルダには人間向けの記入用紙
`L02_INDEPENDENT_VISUAL_REVIEW_FORM_20261110.txt`を追加済み。G0台帳と候補の診断値は
`docs/research/LOCAL_L02_G0_CANONICAL_INVENTORY_20261110.md` に固定した。
Phase4が全ケースで独立PASSになった場合だけPhase5 exact replay、L04正式三点セット、
Golden、本番、実機iPhone受入へ進む。

現時点では、新しいB実装や本番変更を行わない。Aについても、現在候補へ数画素を
足す実装は行わない。H04/H06/H08の失敗構造、observerの盲点、三例共通のowner再構成設計は
設計パックへ固定済みであり、六能力の導入・学習計画も
`LOCAL_L02_OBSERVER_ADOPTION_PLAN_20261110.md`へ固定した。計画上の能力ゲートを通るまで、
候補生成・追加observer・閾値変更・receipt作成を成果として扱わない。

設計パックの正本は
`docs/research/LOCAL_L02_REDESIGN_PACK_20261110.md` とする。

開発全体の工程と、「数画素の改善」を成果として扱わない判定は
`docs/research/MINIMALIZER_DEVELOPMENT_REDESIGN_20261110.md` に固定した。以後の作業は
この工程表に従い、A1の根本設計を通過するまでAの候補修正を行わない。

設計パックに沿うsource-free骨格として、接触component単位のowner solver
`tools/research/local_l02_component_owner_solver.py` と構造テストを追加した。
腕／下着との衝突やinstance重複は部分修正せず、component全体をunknownへ戻す。
この実装は研究層であり、実画像候補・Phase4・owner authorityをまだ成立させない。

次のAサイクルは、設計パック → 三例同時の全身候補1つ → 一括レビューの順に限定する。
通常倍率で変更が識別できない、または一例の改善が別例を壊す場合は、その候補を正式経路
から破棄し、同じ候補を小さく修正しない。

なお、H06/H08の数画素候補では根本品質に届かないことが判明したため、開発方式を
全体owner再構成へ切り替えた。さらに、候補を作ってから少しずつ直す運用も廃止し、
設計パックを先に通す方式へ変更した。開発サイクル、候補にしない変更、完了判定は
`docs/research/LOCAL_L02_DEVELOPMENT_METHOD_RESET_20261110.md`、実装土台と
残差の詳細は `docs/research/LOCAL_L02_SCALE_RESET_20261110.md` を正本とする。

Fashionpedia候補に対するFASHN人体パーサーの単純arm-vetoは、H06/H08で腕観測が
不足しtopが衣装全体を覆ったため設計棄却とした。これはG0台帳にsource-only診断として
記録し、既存候補を画素単位で再編集する根拠にはしない。

追加のATR18/LIP20/FASHN observer出力は、非公開Driveの
`Minimalizer_L02_IndependentObservers_20261110` に16件保存し、ローカルとのファイル名・
サイズreadbackを確認した。腕union vetoと袖保護変種も三例横断では成立しなかったため、
これらは設計棄却のdiagnosticとして保持し、正式候補やPhase4入力にはしない。

component-level owner solverの実画像probeもH04/H06/H08で実行したが、underlayerの
独立observerがない状態ではH06/H08の正衣装回復を失い、Phase4候補にならなかった。
NPZ・receiptは非公開Driveの `Minimalizer_L02_ComponentOwnerSolver_20261110` に保存済み。
次に進む条件は、数画素調整ではなく、外衣・下着・腕・遮蔽順序を同時に観測する
source-only層の設計と三例一括実装である。

Fashionpediaのshirt/topクラスを下着観測として足した派生はH04/H06/H08で改善せず、
非公開Driveの `Minimalizer_L02_ComponentOwnerSolver_BaseLayer_20261110` に履歴保存した。
同一モデルのクラス追加は採用せず、active codeへ残さない。

2026-11-10に実施したlayered garment solverの一括probeも正式候補にはしない。既存の
Fashionpedia外衣proposalとほぼ同じmaskになり、H04/H06/H08の変更量は148/1,926/170px、
H06はIoU悪化だったため、`MICRO_DELTA_ONLY / REGRESSION`として研究履歴に隔離した。
これで「大きな設計名を付けた小差分」を成果として扱わないことを実測で確認した。

### 2026-11-10 最新独立レビュー差分

非公開Driveの最新署名レビューをreadbackした。評価者の独立性、未見性、推論前ラベル非参照、
腕・下着・遮蔽・正衣装保持の意味評価は肯定されている。ただしH06/H08の`いいえ`は画像品質の
不合格ではなく、変更量が通常倍率では小さすぎて判定できないという意味だった。H04は変更画素0。
この二つを混ぜないための差分記録は
`docs/research/LOCAL_L02_REVIEW_DELTA_READBACK_20261110.md`である。

このレビューは小差分Sapiens2候補の確認であり、六能力observerの成立やPhase4 PASSではない。
したがって、L02/Phase4の`HOLD / FAIL`、Phase5/owner認可/Stage8/Golden/productionの`NO_GO`を
維持する。次の候補は三例一括かつ通常倍率で意味改善を判定できる大きさにする。

今後は、observer能力ゲートを通過するまでAのsolver・閾値・receiptを増やさない。
必要能力は外衣、袖、腕、下着、遮蔽関係、人物内instance結合の同時観測であり、
モデル／重みSHA／出力契約が揃った構成だけをH04/H06/H08へ一括probeする。

### 2026-11-10 大規模observer probeの結果

Grounding-DINO + SAM2.1 Hiera Tinyを固定prompt・固定閾値でH04/H06/H08へ一括実行した。
source-onlyであり、人手mask、review JSON、既存ownerは推論入力にしていない。これは
候補作成ではなく、必要能力を持つかを判定するためのprobeである。

結果は三例とも意味FAILだった。H04はarm/sleeve/shirtの各unionがsource alphaの
約97%に達し、H06はarm約89%、sleeve/shirt約99%、H08はarm/sleeve約99%だった。
overlayでも腕・袖が局所化されず、人物全体を覆った。固定prompt方式には可視衣服の
前後関係を表す出力もないため、遮蔽関係能力も成立しない。

判定は`OBSERVER_SEMANTIC_FAIL / CAPABILITY_HOLD`。大きな変更量を理由に候補化せず、
Phase4、owner認可、Stage8、B handoffへは進めない。次に変えるのはpromptや数画素では
なく、外衣・下着・袖・腕・遮蔽関係・instance結合を同時に出力できるアニメ向けobserver
の実行可能なモデル／重み／出力契約である。

その後、対象元画像が透過アニメ人物であることを確認したため、実写向けobserver群から
アニメ向けSee-through body-part parserへ主観測層を切り替えた。`topwear OR (handwear
AND NOT Sapiens2 arm)`の固定規則で一括candidateを作った結果、H04/H06/H08の変更量は
24,317/77,556/74,230px、known-only IoUは0.657878/0.938469/0.967945だった。H06/H08は
有望だが、H04の誤owner過多により全体候補はFAIL。Phase4、owner認可、Stage8 handoffは
行っていない。

次の開発はH04専用修正ではなく、アニメ向け肌／衣装境界observerの三例一括probeである。

なお、observerを増やすこと自体を進捗に数えないため、出力能力の事前ゲートを
`tools/research/local_l02_observer_capability_gate.py`へ追加した。現行See-through
body-part parserは`CAPABILITY_HOLD`（outerwear / underlayer / sleeve / arm /
occlusion_relation / instance_grouping不足）であり、ここを満たす実行可能構成が確定する
まで、Aの候補・Phase4 receipt・Bへのhandoffは増やさない。

### 2026-11-10 大規模観測器の全体パイプラインprobe

数画素のowner修正を繰り返さない方針に従い、body-part parser単体ではなく、See-throughの
LayerDiff3D body/head分解、Marigold深度、PSD組み立てまでを一つの観測器として、固定seed・
固定重み・固定解像度でsource-only実行した。H06/H08はLayerDiff body＋head 20 stepと
Marigold depth、PSD組み立てまで完了した。人手ラベル、既存owner、レビュー結果は推論入力に
使っていない。

| 入力 | 実行結果 | 視覚probe | 正式判定 |
|---|---|---|---|
| H06 | 全体pipeline完了 | topwearに外衣・下層、handwearに袖・手領域、bottomwearに下衣が出力され再構成完了 | 有望だがPhase4未実施 |
| H08 | 全体pipeline完了 | topwearに上着・下層、handwearに袖・手領域、再構成完了。ただしbottomwearは視覚的に使用不可 | 有望だがPhase4未実施 |
| H04 | 全体pipeline完了 | topwearに外衣・下層、handwearに袖・腕領域、再構成完了。ただしbottomwearは視覚的に使用不可 | 有望だがPhase4未実施 |

これはLangSAMの局所部位FAILや、以前の`topwear OR handwear`候補とは別の大きな観測器で
あり、三例すべてで全体実行と再構成まで確認できた。ただしH04/H08の下衣層が視覚的に
使用できず、外衣・下層・袖・腕・遮蔽のowner権限も能力ゲートを通っていないため、候補・
Phase4・owner認可・Stage8 handoffには昇格しない。私的な重みSHA、source SHA、出力場所、
判定は非公開receipt
`SEE_THROUGH_FULL_PIPELINE_PROBE_RECEIPT_20261110.json`に保存した。

次の修正は画素単位ではなく、(1)三例共通で外衣・下層・袖・腕・遮蔽・人物内instanceを
同時に観測できる能力ゲート済み構成を確定し、(2)その構成でH06/H08/H04の全身ownerを
一つだけ再構成し、(3)下衣を含む意味クラス全体を一括レビューし、(4)三例すべてを満たした
場合だけPhase4とowner認可へ進む、の順序に限定する。現在のSee-through全体pipelineは
研究観測として保存するが、bottomwearの欠落と能力契約不足を理由に正式候補へはしない。

### 2026-11-10 解像度変更の一括反証

H04について、LayerDiff部分だけを1280px・固定seed 42・固定NF4重み・30 step・source-onlyで
一括実行した。topwear、handwear、legwearは大きく分離したが、bottomwearには元画像で可視
根拠のない白い下着様レイヤーが出力された。解像度を上げても意味ownerの誤付与は解決せず、
この経路は正式候補へ昇格しない。

保存済みLayerDiff結果を使った新規MarigoldプロセスもCLIP埋め込み初期化時のCUDA illegal-
memoryで停止した。深度・PSD・Stage8三点セットは未生成であり、これは品質PASSではなく
実行環境FAILとして非公開実験履歴に隔離した。

この結果を受け、次のA作業は解像度、閾値、OR/AND、形態学処理、数画素修正ではない。必要能力
（可視層根拠、外衣、下層、袖、腕、遮蔽関係、人物内instance結合）を一つのobserver契約で
満たす候補を確定し、H04/H06/H08を同一条件で一括評価するまで、Phase4・owner認可・Stage8
handoffを増やさない。

