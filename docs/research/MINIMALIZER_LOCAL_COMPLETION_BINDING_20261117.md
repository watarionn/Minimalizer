# MinimalizerLocal 完成結合台帳

更新日: 2026-11-17

## 基準

| 項目 | 値 |
|---|---|
| main | `22d36e88c0b9932cd44e209c8d8be4581098dc62` |
| 採用候補receipt | `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` |
| 本番Worker基準 | `64cfeb76e5f8ff4e93b6810880c68f1996348ede` |
| A observer契約・現行台帳 | `a21f92f0`（契約実装の基点 `00e9ebb9`） |
| B現行head | `4ddc61c2f755ececad6568cda92c1faeac3e991a` |
| B PR | `#465` Draft |

## 今回確認したこと

- L04のH04/H06/H08三点セットは、元画像・Stage8 JSON・展開SVGのSHA照合が3/3で成立。
- 既存の独立評価readbackは、同じ候補SHAに対してL04品質 `PASS`、Golden `PASS`を返す。内部candidate summaryの古いHOLDは、再レビューせずsource-free adapterで分離した。
- Bの三点配信監査は3/3 `PASS`。これはAの意味品質を判定しない。
- Aのsource-free外部入力到着台帳は `a21f92f0` に更新され、六能力observer未到着の
  状態を現行B結合へ反映している。明示的な三組遮蔽契約、checkpoint/別人物学習の
  二経路intake監査、到着後のcmd runbookを追加したが、実資材はなお
  `TRAINING_INPUT_HOLD` である。
- A intake監査は、候補品質をPASSさせるものではないまま、正本の8要素observer出力契約を
  `observer_capabilities` として明示出力するよう更新した。B最終ゲートも同じ配列を照合する。
- 現行WorkerへのPC private HTTPSは、PNG成功2経路、415/429/503、入力・出力SHA読戻しを再確認した。iPhoneは現行Workerで未受入。
- L07候補はcache-first、世代固定、クエリ/URLエンコード別名固定、旧世代保持を実装した。
  この台帳のB候補SHAは、独立L04結合readbackまで含む現行PR #465の先端へ更新している。
- 今回のL04/L05/L07/release-binding/receipt-auditテスト69件、実SW Node 3件がPASS。
  A側のobserver intake関連テスト89件もPASSしたが、これはAの実資材到着やPhase4
  合格を意味しない。
- `audit_local_completion_release.py` で、A、Phase4、Phase5、L04/L05/L07、
  実機受入、回帰、保存の9 receiptをsource-freeに一括監査できる。
- completion gate CLIの直接cmd起動経路を修正し、`python tools\research\audit_local_completion_release.py --help`
  を実行できることと、その回帰テストを追加した。
- BのL04/L05/L07/release関連選択テストを現行headで再実行し、Python `79 passed`、
  実SW `3 passed`、SW構文検査、`git diff --check` がPASSした。
- 旧L05 owner receiptを現行候補・Workerへ結び付ける
  `audit_local_l05_current_worker_binding.py` を追加した。receipt本体のSHAを別binding
  JSONへ固定し、現行Worker以外のiPhone receiptを自動HOLDにする。これはrelease許可ではない。
- 実receiptへの適用結果をsource-freeで確認した。現行PC receipt
  `e3a4b368205fb7675cccd487a5bbcc5072abf829afabe78c462ed3d7f6080d41` は現行候補・Worker
  binding `PASS`。既存iPhone receipt `06f09cfba8958a7214a86157ea19ad64c49c3ba876e65ca2c908c9cf70b91fea`
  は旧Worker `c68dc17…` のため `IPHONE_WORKER_COMMIT_MISMATCH`。後者は現行受入へ再利用しない。
- 現行WorkerでiPhoneを再受入した後は、raw receiptの `production_commit` を
  `64cfeb76e5f8ff4e93b6810880c68f1996348ede` にし、raw JSON SHAをbinding JSONへ記録して、
  `audit_local_l05_current_worker_binding.py` を実行する。現行Worker・Safari・PWA・offline・
  fallback・Drive readbackが揃ったreceiptだけがbinding `PASS`になる。
- 現行Worker用のiPhone binding生成CLI
  `tools/research/prepare_local_l05_iphone_binding.py` を追加した。raw receiptからSHAのみを
  取り出してbinding JSONを生成し、旧Worker receiptは生成前に `HOLD` とする。raw receiptや
  画像・スクリーンショットはGitHubへ保存しない。追加テストを含む現行選択テストは
  Python `79 passed`、実SW `3 passed`。
- 既存の実iPhone receipt（raw SHA
  `06f09cfba8958a7214a86157ea19ad64c49c3ba876e65ca2c908c9cf70b91fea`）をこのCLIへ渡した
  実行は `EXIT=2 / IPHONE_WORKER_COMMIT_MISMATCH` となり、binding出力ファイルは生成されなかった。
- 現行WorkerでのiPhone受入からbinding監査までを一度で行うcmd手順を
  `docs/research/LOCAL_L05_IPHONE_CURRENT_WORKER_RECEIPT_RUNBOOK_20261117.md` に追加した。
  実機受入receiptが届くまでは、手順の実行結果を推測せずL05をHOLDとする。
- 本番runtimeを再読し、checkout SHAは現行Worker `64cfeb76e5f8ff4e93b6810880c68f1996348ede`、
  private HTTPS `/health` はHTTP `200`、`active_production_route=zerobase2`、
  `zerobase2_authorized=true`、`runtime_error=null` だった。これはWorker反映とhealthの証拠であり、
  iPhone受入、Aの意味品質、正式releaseを完了扱いにはしない。runtime checkoutの既存未追跡
  `dist/` は変更していない。
- 現行候補SHA `381b0b5a…` に結び付いたL04 v12独立readbackは、候補監査・B delivery・独立性を
  `PASS`、`L04_formal=PASS`、`Golden=PASS` と記録している。ただし同じreadbackは
  `production=NO_GO`、`release_authorized=false` であり、L04/Golden PASSだけで正式releaseへ
  進めない。別のL08 readiness receiptにあるiPhone証拠はWorker `c68dc17…` を参照するため、
  現行Worker証拠列へ結合しない。
- 2026-11-11の独立Phase4 receiptは内部ケースの候補配列SHA
  `36bbb780…`、`6034f911…`、`8daafac9…` を記録しているが、採用候補receipt
  `381b0b5a…` への明示bindingを持たない。また同receiptの `phase5=NO_GO` と、別ファイルの
  Phase5入力監査 `phase5=READY` は同じ意味ではない。したがって、これらを現行候補の
  Phase4/Phase5正式PASSへ自動流用しない。現行候補へ結合した独立Phase4とPhase5 exact replayが必要である。
- このbinding欠落を埋めるsource-free検証器
  `tools/research/bind_local_l02_phase4_candidate.py` と4件のfail-closedテストを追加した。
  三例のsource SHA・candidate配列SHAを明示するbinding manifestがない限り、採用候補
  `381b0b5a…` へ結合せずHOLDにする。今回の検証はPython `28 passed`、release権限は付与しない。
- 実在する旧Phase4 receiptと既存のcandidate-bound Phase4 input manifestをこの検証器へ渡した
  実行結果は `HOLD / INVALID_BINDING_SCHEMA` だった。既存manifestを正式bindingへ昇格させず、
  新しい明示binding manifestの到着を要求する。
- 既存の `minimalizer-l02-candidate-bound-phase4-20261113-v8` は、Phase5入力監査だけを見ると
  `READY` だが、H04/H06の候補SHAは最終独立評価receiptの配列SHAと異なる旧base候補であり、
  H04/H06/H08のstage設定にも `observer_capability_status=HOLD`、
  `observer_formal_phase4=FAIL` が残る。したがって現行候補のPhase4証拠へ昇格しない。
- 最終release gateは、従来の `six_capabilities=true` 要約フラグだけでは通らないよう、
  A正本の8要素出力契約（外衣・下層衣装・袖・腕・3種の遮蔽・instance分離）を
  `observer_capabilities` として個別照合する実装へ更新した。新規テストを含めPython `25 passed`。
- 同じ最終gateに、L04の元画像・Stage8 JSON・展開SVGの個別SHA結合と、L07の世代固定・
  rollback可能性を必須化した。形式だけのL04/L07 PASSを正式releaseへ流用しない。
- 実在するL04 v12 receiptへ更新後のadapterを適用し、三点SHA結合は `PASS`、独立レビューも
  `PASS`のままだが、`production=NO_GO`、`release_authorized=false`、Phase5昇格未許可だった。
  現行BのSW/route静的監査はgeneration `minimalizer-local-20261117-2`、世代固定・rollback保持・
  offline shellを `PASS` としたが、`live_iphone_e2e_verified=false`、実機受入には流用しない。
- 同じ静的監査を本番runtime checkout `64cfeb76e5f8ff4e93b6810880c68f1996348ede` に適用すると、
  `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK` でFAILした。runtimeのSWは generation
  `minimalizer-local-20261107-1` で、activate時に旧世代cacheを削除する。リポジトリ側の
  `minimalizer-local-20261117-2` 契約とは不一致であり、runtimeの未追跡 `dist/` は変更していない。
  現行Workerの健康状態PASSを、L07正式反映PASSへ読み替えない。
- runtime再結合前後のowner-only確認手順を `docs/research/LOCAL_L07_RUNTIME_REBIND_RUNBOOK_20261117.md`
  に追加した。これは反映を実行せず、未追跡 `dist/` を保護したまま、SHA・SW監査・health・
  rollback・実機受入の順序を固定する。
- L07静的監査CLIにfail-closed JSON出力を追加し、runtimeへ実行した結果を
  `C:\Work\Temp\L07_RUNTIME_AUDIT_20261117.json` に保存した。結果は
  `status=HOLD`、`release_authorized=false`、失敗理由は
  `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK`。source側とrelease gate関連の選択Pythonテストは
  `39 passed`。
- 最終release gateのL07条件に、静的な世代固定・rollbackだけでなく、現行Worker runtimeの
  SW監査PASSとruntime generation結合を追加した。source側だけのPASSで本番不一致を隠せない。
- L07静的監査の出力にも `runtime_sw_audit_pass=false`、`runtime_generation_bound=false` を
  明示し、source監査receiptをruntime受入receiptへ誤流用できないようにした。

## 検証範囲の注意

- B変更に関係する選択テスト、実SW、構文検査、差分検査はPASS。
- リポジトリ全体のpytestは、現行の基底環境と隔離QA環境の双方で、既存テストが
  要求する任意依存（`scikit-learn`、`playwright`、`torch`、`fastapi`、
  `scikit-image`等）の未導入によりcollection errorとなった。
- このcollection errorをB実装のPASSや全体回帰PASSへ読み替えない。全体回帰を
  正式PASSへするには、依存を固定したCI/QA環境を別途用意する必要がある。

## 完成結合ゲートの現状

現行のL04/L05/L07証拠をsource-free結合ゲートへ入力した結果は次のとおり。

```text
status: HOLD
release_authorized: false
```

理由:

- L04品質は独立評価readbackでPASSだが、productionは `NO_GO` のまま。
- L05はPC側証拠が揃ったが、iPhone受入を含む正式L05はHOLD。
- L07は静的契約PASSだが、現行Workerでの実機iPhone受入が未確認。
- owner操作・本番反映が未完了。
- 旧L08 readinessは別Worker commitを参照しているため、現行Workerの正式証拠にはしない。

## 残ゲート

1. Aの六能力observerまたは別人物データ学習を成立させる。
2. H04/H06/H08を同一設定でsource-only推論する。
3. 独立Phase4をPASSさせる。
4. H08 owner認可receiptとPhase5 exact replayを同一候補へ結合する。
5. L05/L07 receiptへ候補SHA・Worker SHAを明示結合する。
6. 現行WorkerでiPhone Safari/PWA、PNG/SVG、機内モード復帰、fallback/rollbackを受入する。
7. AのPhase4 PASS後にL04 production/GoldenとPhase5 exact replayを同一候補へ昇格する。
8. owner承認、本番反映、Drive読戻しを完了する。

この台帳は完成宣言ではなく、古い実験・別候補・別Workerの証拠を現行候補へ誤結合しないためのsource-free記録である。
