# MinimalizerLocal 完成結合台帳

更新日: 2026-11-17

## 基準

| 項目 | 値 |
|---|---|
| main | `22d36e88c0b9932cd44e209c8d8be4581098dc62` |
| 採用候補receipt | `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` |
| 本番Worker基準 | `64cfeb76e5f8ff4e93b6810880c68f1996348ede` |
| A observer契約・現行台帳 | `b9c72162`（契約実装の基点 `a21f92f0`） |
| B現行head | `100cd207bdace40b266969695dff87382f1623c2` |
| B PR | `#465` Draft |

## 今回確認したこと

- L04のH04/H06/H08三点セットは、元画像・Stage8 JSON・展開SVGのSHA照合が3/3で成立。
- 既存の独立評価readbackは、同じ候補SHAに対してL04品質 `PASS`、Golden `PASS`を返す。内部candidate summaryの古いHOLDは、再レビューせずsource-free adapterで分離した。
- Bの三点配信監査は3/3 `PASS`。これはAの意味品質を判定しない。
- 既存の候補三点セットを非公開 `minimalizer-l04-production-bundle-20261117` へ再配置し、
  manifest SHA `01584ca9f75e984c28a1ffc85faa468f9ab2f0f59c6d9e354ea7d6bc1ad7ab08` を固定した。
  L04 production bundle loaderは候補SHA、H04/H06/H08各元画像・Stage8 JSON・展開SVGの
  9 SHA、相互リンク、安全なSVGを照合して `PASS` を返した。ブラウザ再展開も3/3 `PASS`。
  これは非公開bundleの準備完了であり、runtimeへの反映・実機受入を意味しない。
- Aのsource-free外部入力到着台帳は `b9c72162` に更新され、六能力observer未到着の
  状態を現行B結合へ反映している。明示的な三組遮蔽契約、checkpoint/別人物学習の
  二経路intake監査、到着後のcmd runbookを追加したが、実資材はなお
  `TRAINING_INPUT_HOLD` である。
- A intake監査は、候補品質をPASSさせるものではないまま、正本の8要素observer出力契約を
  `observer_capabilities` として明示出力するよう更新した。B最終ゲートも同じ配列を照合する。
- 現行WorkerへのPC private HTTPSは、PNG成功2経路、415/429/503、入力・出力SHA読戻しを再確認した。iPhoneは現行Workerで未受入。
- L07候補はcache-first、世代固定、クエリ/URLエンコード別名固定、旧世代保持を実装した。
  この台帳のB候補SHAは、独立L04結合readbackまで含む現行PR #465の先端へ更新している。
- 今回のL04/L05/L07/release-binding/receipt-auditテスト69件、実SW Node 3件がPASS。
  A側の現行observer intake/capability/training関連テスト67件もPASSしたが、これはAの実資材到着やPhase4
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
- 今回のowner許可に基づくprivate L04 bundle manifestは、L04専用の
  `production=GO` / `release_authorized=true` としてloader検証を通過させた。ただし全体の
  release gateはA Phase4/Phase5、L07 runtime、現行iPhone受入、L06結合が未完了のためHOLDである。
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
- Phase4最終gateに、未見データ、推論前ラベル未使用、レビューJSON未使用を必須化し、
  candidate binding adapterの検証済みprovenanceを最終receiptへ引き継ぐようにした。
- L06の現行候補結合adapterとcmd手順を追加した。Phase14 summary自身に候補SHAがなく、
  ブラウザ/性能receiptも同じ候補SHAへ結合されていない場合は、旧Approved18→78結果を
  現行候補へ流用せずHOLDにする。新adapterの選択テストは `43 passed`、`git diff --check`
  もPASSした。
- L07のowner runtime結合adapterとreceipt手順を追加した。runtime Worker SHA、SW世代、
  旧世代保持、rollback、health 200、`runtime_error=null`、`zerobase2_authorized=true`を
  一つのsource-free receiptへ結合するが、owner反映済みの明示receiptがない限りHOLDにする。
  現行runtimeの監査結果は引き続き `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK` である。
  L06/L07を含む選択テストは `47 passed`。
- Aのローカル資材をメタデータだけ再確認し、19-part SAMの不足能力、Fashionpedia/Sapiens2の
  現行contract・三例receipt不足をsource-free台帳へ記録した。重みの存在だけでobserverを
  昇格させず、Aの現状は `CAPABILITY_HOLD` / `TRAINING_INPUT_HOLD` のままとした。
- CubismPartExtrの新しいbuild領域を再確認したが、Core SDK、Samples、`PartExtr.exe`はなく、
  既存presetのbuildも `MSB1009 / PartExtr.vcxproj` 不在で終了した。抽出実行可能状態や
  別人物catalogの到着へ読み替えず、Aは引き続きHOLDとする。

## 完成目標の正本

実装・手順・所有者操作を、次の目標IDと依存関係で管理する。各目標のPASSは、
記載したreceiptまたは実行結果が現行候補 `381b0b5a…` と、必要な場合は本番Worker
`64cfeb76…`へ明示的に結合されている場合だけ成立する。v5候補、旧Worker、旧候補の
結果は再利用しない。

| ID | 目標 | 主な実装・手順 | 現状 | 完了条件 |
|---|---|---|---|---|
| G0 | 基準を凍結する | main SHA、候補receipt SHA、Worker SHA、A/B branch、非公開成果物の保管境界を台帳へ固定 | PASS | source-free台帳と各SHAのreadbackが一致 |
| G1 | 六能力observer入力を成立させる | 実行可能checkpoint、または別人物データ学習経路を到着させ、重み/SDK/catalog SHAを記録し、intake監査を実行 | HOLD | 外衣・下層衣装・袖・腕・3組遮蔽・instance分離、unknown分離、人物分離、固定revisionがPASS |
| G2 | H04/H06/H08を同一設定で新規推論する | 署名済み元画像だけを推論入力にし、ラベル・評価マスク・レビューJSONを推論前に読まない。unknownを陰性化しない | HOLD（G1待ち） | 3例のsource SHA、設定SHA、candidate配列SHA、推論時provenanceが揃う |
| G3 | Aの意味品質を独立Phase4でPASSさせる | 凍結候補を独立評価者へ渡し、4/8連結、穴、重要部位、遮蔽、排他的owner、正衣装保持を評価 | HOLD（G2待ち） | 未見、推論前ラベル未使用、評価者独立、意味評価完了、出力凍結、review JSON非入力、Phase4 PASS |
| G4 | H08 owner認可を候補へ結合する | H08のowner authority receiptを、候補配列SHA・owner SHA・独立レビューへ明示結合 | HOLD（G3待ち） | `43d164…`を含む現行候補向けowner receiptがPASS。承認は品質判定を代替しない |
| G5 | Phase5 exact replayを行う | Phase4 PASS候補と同じsource/config/outputを使い、別候補への差替えや再調整をしない | HOLD（G3/G4待ち） | 3例すべてのsource/candidate/output SHAと同一設定が一致し、Phase5 PASS |
| G6 | L04正式三点セットを昇格する | 元画像・Stage8 JSON・展開SVGを各SHAで照合し、独立レビュー、Golden、production bundleを同一候補へ結合 | 部分PASS / 昇格HOLD | G3/G5後にL04 formal/Golden/production GO、三点SHA一致、release falseが解除 |
| G7 | L07を本番runtimeへ安全に反映する | source監査→owner承認済み反映→runtime SHA/SW generation/hash再読込→rollback確認。`caches.delete`等を禁止 | adapter実装済み / runtime HOLD | runtime監査PASS、世代結合、旧世代保持、rollback可能、health 200、runtime errorなし |
| G8 | L05を現行Workerで受入する | PC確認後、現行runtimeのiPhone Safari/PWAでPNG/SVG、機内モード復帰、429 Retry-After 2、503/fallback/再試行を実施 | PC PASS / iPhone HOLD | iPhone raw receiptのWorker SHAが `64cf…`、binding監査PASS、Drive readback PASS |
| G9 | L06回帰と表示性能を結合する | Approved18→78、Golden、通常ブラウザ、PNG/SVG表示、性能を同一候補で確認 | adapter実装済み / 現行証拠HOLD | 現行候補・Workerへ結合した回帰receiptがPASS |
| G10 | 最終release gateを通す | A、Phase4、Phase5、L04、L05、L07、L06、保存のreceiptを一括監査 | HOLD | `release_authorized=true`以外を正式採用しない |
| G11 | owner shipと保存を完了する | owner承認、許可対象だけを本番反映、PC/iPhone readback、Drive読戻し、source-free台帳更新 | 未実施 | 本番SHA、成果物SHA、独立評価、実機受入、復旧結果が同一版で一致 |

### 依存関係

```text
G0 基準凍結
 ├─> G1 六能力observer入力 ─> G2 同一設定の新規推論 ─> G3 独立Phase4 PASS
 │                                                    └─> G4 H08 owner認可
 │                                                         └─> G5 Phase5 exact replay
 │                                                              └─> G6 L04正式昇格
 ├─> G7 L07 runtime再結合 ─> G8 現行Worker iPhone受入
 └─> G9 L06回帰・性能

G6 + G8 + G9 + 保存証拠 ─> G10 最終release gate ─> G11 owner ship/保存/完了
```

### 作業順序と停止条件

1. まずG1を実資材到着まで進める。到着後はintake監査、SHA固定、source-only推論を一回の
   連続した作業として行う。H04/H06/H08のラベルや評価マスクを推論入力へ戻さない。
2. G2の候補を凍結してからG3/G4を一度だけ依頼する。小さな画素修正を反復せず、失敗した
   owner・遮蔽・袖・下層衣装の構造原因を次の大きな実装単位へまとめる。
3. G3 PASS後にG5を行い、その候補のままG6を正式昇格する。G3前のL04 PASSは配信三点の
   整合性証拠であり、A品質の代替ではない。
4. BではG7のruntime再結合をowner承認済み手順でのみ実施する。runtimeの未追跡`dist/`を
   直接削除・上書きしない。G7 PASS前のiPhone結果は現行Worker受入へ流用しない。
5. G8/G9とDrive読戻しを揃え、G10の一括監査がPASSになるまでmerge・正式releaseをしない。
6. G10 PASS後にだけG11を行い、反映後のhealth、通常入口、PNG/SVG、rollbackを再読込する。

### 現時点の次の一手

今すぐ実行できるsource-free作業は、G0の台帳整合性維持、G1到着時のintake実行環境、
G7 owner runtime再結合手順の保全、G9の現行候補binding準備までである。G1の実資材、
現行runtimeのowner反映、現行WorkerでのiPhone操作は、所有者または外部入力が必要なため、
証拠を推測してPASSにはしない。

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
