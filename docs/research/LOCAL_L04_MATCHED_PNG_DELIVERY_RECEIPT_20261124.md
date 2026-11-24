# Local L04 PNG/SVG同一候補配信記録

作成日: 2026-11-24  
状態: `MERGED_AND_LIVE / API_H04-H06-H08_PNG_SVG_PASS / CHROMIUM_H04_OFFLINE_WORKER_RECOVERY_AND_ISOLATED_SW_ROLLBACK_PASS / APPROVED18_78_PASS / OWNER_GOLDEN_APPROVED_FOR_381B / PERFORMANCE_OBSERVED_NO_CAP / IPHONE_EXACT_RECEIPT_ACCEPTANCE_PENDING`

## 固定対象

- 候補receipt SHA-256: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- 実機Worker基準commit: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- 実装PR: `#467`（merged）
- 実装main commit: `191f93d85e248f02003ac9835e58484a6d5c177f`
- private bundle ZIP SHA-256: `c489fb5b11c209c491faf5c6aa1d4bdd20652e9f26efad56f4ee871e9a671efe`
- Drive読み戻し: ZIPのサイズ`964667` bytes、SHA-256がローカル値と一致
- 2026-11-24にDrive上の同名bundleをメタデータ確認後、認証済みfetchで再読戻しした。サイズ`964667` bytes、SHA-256 `c489fb5b11c209c491faf5c6aa1d4bdd20652e9f26efad56f4ee871e9a671efe`でローカルbundleと一致。読戻しsource-free receiptは[LOCAL_L04_DRIVE_READBACK_20261124.json](evidence/LOCAL_L04_DRIVE_READBACK_20261124.json)、SHA-256 `c6c2e0d83a8024ccd3eb24172b6fa824c0b09416ffdfc0b9a4894c4afc4c19c8`。一時読戻しコピーはハッシュ照合後に削除し、Driveの非公開IDや画像データはGitHubへ記録していない。

## 三点セットとPNG派生物

| ケース | 元画像SHA-256 | Stage8 JSON SHA-256 | 展開SVG SHA-256 | 透過PNG SHA-256 | 寸法 |
| --- | --- | --- | --- | --- | --- |
| H04 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | `82a7df6ed4a7cbce068c9038cd8ce648448308df2134c07b8e61c1cff1d2c67b` | `feda80bb7405aa6758a839bf2bbef6147b64620d5a20b31c0d9ee7f694d627f4` | `dc5467db8fdce139ad76cc88e3087e68037070d675cb7ea72180f51901167358` | 453×1400 |
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `e3a25866d40bf31582d9cc4bddba22c8055d31bef3930d32e9fca99d8b9782aa` | `1493d7dbeecce0563baa0bb86bcb4230d01f10db14a4a69919d11b841a41ea16` | `cf4c08ff52256f75395a6eb3e3c32065701690d998d1f40dd2f61d1454f2bf3b` | 2000×2000 |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `e87bd3c4a5f687b6ab155a4b76f0afab8b542bcb1934d38bef0259a4adb730f2` | `712337aa48bdfad3bbda778b903478bc1b4cec1d42e110c95d249b8f82a4860c` | `9aa6aed7910a7a41b7568ff8975ff8bf6125180f672d61643238b203e4eedce7` | 2000×2000 |

PNGは展開SVGから`@resvg/resvg-wasm` 2.6.2、WASM SHA-256 `22bf6e9f9a100d972da0411a69c5ba504367fc1fa87b3b64e3f35e53926d2d70`、`fit=original`で生成した。三画像とも再生成SHAが一致し、RGBA/alphaを保持する。ソース、JSON、SVG、PNGはprivate Driveのbundleだけに保存した。

## 実装と検証

- v1 manifestのSVG配信は維持し、v2 manifestでPNG派生物のSHA・元SVG SHA・寸法・renderer buildを検証する。
- 正式入力SHAが一致したPNG要求は、推論を再実行せず、同じ候補のSHA固定PNGを返す。PNGが欠落・不一致なら別候補へfallbackせず503で停止する。
- SVG要求は既存の展開SVGを返す。通常入口のPNG/SVG両方にreceipt SHAとケース識別子を含める。
- PR commit `6630d9f140506242f82bba3dad148025f10529e0`のFocused tests: `60 passed`（LocalWorker、L04 source/Stage8/SVG gate、delivery audit、L07 privacy audit）。同じ差分をmain `191f93d8`へsquash mergeした。
- real private inputsを用いたTestClient E2E: H04/H06/H08のPNG/SVG全6要求がHTTP 200、receipt SHAと各成果物SHAがmanifestに一致。
- Node/Python構文確認: PASS。派生PNG再生成のSHA一致: 3/3。
- 本番Workerは基準commit `64cfeb76e5f8ff4e93b6810880c68f1996348ede`上の専用runtimeで稼働。起動スクリプトを専用runtime・AppDataのv2 manifest・receipt `381b0b5a…`へ修復し、変更前の4コードファイルと起動スクリプトをprivate backupへ退避した。
- 起動後のprivate HTTPS `/health`: `ready=true`。通常API入口でH04/H06/H08のPNG/SVG全6件がHTTP 200、receipt SHAおよび成果物SHA一致。
- PNG HTTPS総時間: H04 `572.5 ms`、H06 `413.9 ms`、H08 `473.2 ms`。Worker計測はそれぞれ`315.8/227.0/268.2 ms`。
- 2026-11-24のWorker再起動後、旧worker/manager PID `32676/32788`から新worker PID `12164`へ移行し、private HTTPS `/health`は再び`ready=true`。同一の通常API入口へ6要求を送り、PNG/SVG全件HTTP 200、receipt `381b0b5a…`、H04/H06/H08識別子、manifest成果物SHAを照合した。再起動後のclient elapsedはH04 PNG/SVG `283.2/295.1 ms`、H06 `209.6/277.7 ms`、H08 `198.7/205.1 ms`。source-free readback receipt SHA-256 `31a49b554f1a7e77d739c734c1b5c1d305658cd3d8152b3ffb9f7ba3d2e9fe1f`（6要求・3ケース、原画像/応答画像はreceiptへ埋め込みなし）。
- この再起動後readbackはAPIの候補・成果物一致を確認したもの。通常Worker推論の旧記録H04 `22.6 s`と、同一候補からの固定成果物配信の各計測値を区別して記録する。ユーザーは数値上限を採用していないため、L06では計測値を観測結果として保存し、性能の閾値PASS/FAILは付けない。
- 実PC Chrome通常画面で署名済みH04を選択し、変換、プレビュー、PNG・SVG保存メッセージを確認。保存ファイルはPNG `dc5467db…`、SVG `feda80bb…`でmanifestと一致。
- 不正なtext/plain入力はprivate HTTPS APIでHTTP `415` JSONとなった。
- L07 Service Workerはgeneration `minimalizer-local-20261124-1`。静的監査`23 passed`、generation一致、cache-first、cache miss時fail-closed、旧generation cache削除なしを確認。Chrome内部診断URLはComputer Useで開けなかったが、後述のheadless Chromeブラウザ試験で現行generationのoffline shellを確認した。
- 2026-11-24、隔離したheadless Chrome `157.0.8103.79`で現行private HTTPSとSW generation `minimalizer-local-20261124-1`を用いたブラウザE2Eを実施。署名済みH04元画像を画面から選択し、変換プレビュー（453×1400）、PNG保存、SVG保存まで通常UI経路で完了。保存SHAはPNG `dc5467db…`、SVG `feda80bb…`でreceipt `381b0b5a…`のmanifest値に一致。
- 同じブラウザでネットワークをofflineにし、SWキャッシュからshellを再表示。元画像の変換要求は画面に「LocalWorkerへ接続できません」と表示され、online復帰後に同じ画像を再送してプレビューとPNG/SVG保存に成功。previewまで`766 ms`。これはレシート381の観測値として記録し、上限値による合否判定には用いない。
- Worker-stop障害も2026-11-24に同じsource-free H04経路で確認。処理中でないことをhealthで確認してlistenerだけを停止すると、private HTTPS通常UIはHTTP 502を含む接続案内を表示。監視プロセスがWorkerを自動復帰させ、新listener PID `37876`でhealth `ready=true`となった後、同じ画面から再試行し preview `406 ms`、PNG/SVG保存SHAともmanifestと一致。source-free JSONは[LOCAL_L07_WORKER_STOP_RETRY_READBACK_20261124.json](evidence/LOCAL_L07_WORKER_STOP_RETRY_READBACK_20261124.json)、SHA-256 `786c8da303f247b879c390d46d71fd9a26b3921c351fa7af93326306a52cbe03`。
- 2026-11-24 19:37 JST、所有者がCMDで起動手順を実行した後、常駐supervisorを維持してWorker PID `39948`を停止。PID `36136`で再起動し、loopback HTTP `28764`とprivate HTTPS `28765`のhealthがともに`ready`、`zerobase2` authorized、runtime errorなし、idleを確認。runtime commit `64cfeb76…`、receipt `381b0b5a…`、manifest SHA `f9ab8fd7…`を同時に照合した。source-free receiptは[LOCAL_L07_WORKER_RESTART_READBACK_20261124.json](evidence/LOCAL_L07_WORKER_RESTART_READBACK_20261124.json)、SHA-256 `c841606f783600632628ce6e526d2c4bd7c7ba0ac52f06135109a2c70adafc35`。Worker再起動後のhealth確認であり、実機iPhoneやL02品質を承認するものではない。
- SW世代更新/rollbackは、現行`sw.js`を使った隔離localhost originのheadless Chrome試験でv1→v2→v1を実行。v2は旧ページが閉じるまでwaiting、両世代cacheを保持してactivation。rollbackでもv1がwaitingを経て有効化し、v1 shellを再表示。試験origin/cacheを後片付けした。source-free receiptは[LOCAL_L07_SW_GENERATION_ROLLBACK_SIM_20261124.json](evidence/LOCAL_L07_SW_GENERATION_ROLLBACK_SIM_20261124.json)、SHA-256 `6cd19e26ff605f17b28dbbce470ae8600473b941c41d7e987f3d548f365e86f2`。これは現行SW実装の隔離シミュレーションであり、本番private HTTPS上の世代rollbackやiPhoneのrollback受入を証明しない。
- ブラウザreadback source-free JSON: [LOCAL_L07_BROWSER_READBACK_20261124.json](evidence/LOCAL_L07_BROWSER_READBACK_20261124.json)、SHA-256 `ddf11b0cab0b7d938dc5b768d6f59ebb9d48032522f94f08e24eeeb5e12d94bc`。このheadless記録では通常UI、SW offline shell、offline error、online retryをPASS。実GUI Chromeの操作は直後のGUI receiptで別途確認済み。実機iPhoneの同一receipt受入と本番private HTTPS上のSW世代rollbackは未確認。
- 2026-11-24にGitHub main `0673449a…` のgate実装でApproved18/78の既存証拠を再検証した。Approved18は入力SHA 18/18、approved-reference SHA 18/18、保存済み構造評価18/18でPASS。Approved78はScene/Candidate証拠78/78、replay complete、MigrationGate PASS。Source-free binding JSONは[LOCAL_L06_APPROVED18_APPROVED78_READBACK_20261124.json](evidence/LOCAL_L06_APPROVED18_APPROVED78_READBACK_20261124.json)、SHA-256 `3241e570a6410002738a0267dd991c80e0e98e88175266515eee40049e7c6248`。詳細gate receipts: [Approved18](evidence/LOCAL_L06_APPROVED18_GATE_20261124.json) / [Approved78](evidence/LOCAL_L06_APPROVED78_GATE_20261124.json)。実Workerの主要4 runtimeファイルは同じmain SHAのファイル内容と一致し、稼働PID `3556`、候補receipt `381b0b5a…`を同時に読み戻した。
- このApproved18/78 gate再実行は保存済み評価・Scene/Candidateを照合するもので、78枚の新規モデル推論や新規人手Golden審査ではない。Approved78のcalibration metricも非gating。現行L04候補のmanifest SHA `f9ab8fd7…`はreceipt SHA `381b0b5a…`、`Golden=PASS`、owner production authorizationを結合している。ワタルの既存承認と署名済み評価を再利用し、評価者へ再レビューを依頼しない。
- L06性能は旧通常推論H04 `22.6 s`、現行固定PNG配信のH04/H06/H08 client elapsed、headless browser preview `766 ms`を同一candidate記録として保持する。数値capは採用されていないため、状態は`OBSERVED_NO_CAP`とし、速さを品質PASSへ読み替えない。
- 画像semantic P0/P1改善数: 0。これは配信整合性の変更であり、Aの意味品質を主張しない。

2026-11-24 20:09 JST、Worker PID `36136`だけを入れ替え、常駐supervisor PID `38552`を維持してPID `40596`で再起動した。20:15 JSTにloopback HTTP `28764`とprivate HTTPS `28765`の両healthが`ready`、`zerobase2` authorized、runtime errorなし、idleを再確認。Worker runtime `64cfeb76…`、採用receipt `381b0b5a…`、production manifest SHA `f9ab8fd7…`も照合した。source-free receiptは[LOCAL_L07_WORKER_RESTART_READBACK_20261124T2009.json](evidence/LOCAL_L07_WORKER_RESTART_READBACK_20261124T2009.json)。今回の確認は起動・readbackのみで、iPhone受入やL02意味品質を承認しない。

## A Phase4・Phase5の候補一致 readback（2026-11-24）

- 既存の署名済み独立レビューreceipt SHA-256: `bab6a3b873cd7480c3b940202b4219203798d499b577a90cac45edf98a71022f`。固定source SHA、freeze receiptのcandidate SHA、署名・未見性・推論前ラベル非参照・評価者独立・意味評価を既存verifierで再照合し、H04/H06/H08全件 `Phase4=PASS`。
- H04 candidate SHA `36bbb7803fc8bc55186d78e02cb68d41487e7c784b53e0422cac971b39ae1840`、H06 `6034f91150a49146a0ef8badd5d16c1ae5f659dc1db850a482426d01eda29335`、H08 `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091`。三例ともレビューreceiptと同一の候補SHA。
- H08 owner-authority receipt SHA-256: `50207cf17d22cca5c962500a4490de65f83073b2a031313521331dd304caae99`。凍結owner `43d164d9…` からレビュー対象candidate `8daafac9…` への昇格承認に結合し、Golden/productionは引き続き未認可。
- 上記Phase4 candidateと同一のsource SHA・candidate SHAを持つprivate Phase4 bundleについて、Phase5入力監査を再実行し3/3 `READY`。監査receipt SHA-256: `06439a61c1cc71c7eef3c103fb9207bf6bd769f203da4f732aa6bf0514d0aee8`。
- SHA固定元画像を使い、`scripts/zerobase2_phase5_structure.py`（Git blob `2b810f4029be35eea9929020023566b34c1257e`）でH04/H06/H08 Phase5を隔離出力先へ再実行。3例すべて `pass=true`、孤立主要部位0、missing arm/core/accessory attachmentなし、occlusion cycle 0。再生成graph SHAはH04 `ff50ac3d…`、H06 `3842e0f3…`、H08 `8d3feeb6…`で、既存の同一候補Phase5 graph SHAと全件一致。
- 4/8連結と穴の既存candidate-freeze比較も照合済み。H04のcomponent数5/5・hole数2/2は不変。H06は4連結9、8連結8、4連結hole25、8連結hole17が不変。H08はowner 1でcomponent 29/22・hole 3/1、owner 2でcomponent 14/11・hole 3/1が不変。独立レビューは正衣装保持、誤owner除去、袖owner排他、遮蔽・重要部位保持、未知を陰性扱いしないことを三例すべて確認。
- **このA結果は現行L04 production bundleと未一致。** production bundleのStage8 candidate SHAはH04 `5b568993…`、H06 `87278640…`、H08 `8daafac9…`。したがって独立Phase4/Phase5 PASSを、receipt `381b0b5a…` のH04/H06へ遡及適用しない。現行bundle/Workerは変更していない。
- 6能力observerの未完了も別ゲートとして残る。既存checkpointは外衣・袖・腕までで、下層衣装・ペア別遮蔽3種・人物内instanceを同一observer契約で出力しない。今回のPhase4/Phase5再現はこの不足を埋めたものではない。

## 残ゲートと次の変更

1. L06 Goldenはmanifest SHA `f9ab8fd7…`上でPASS、Approved18/78は保存済み証拠の再照合でPASS。性能は候補結合の計測を保存済みで、数値capは採用せず`OBSERVED_NO_CAP`とする。視覚レビューを評価者へ繰り返し依頼しない。
2. PC Chrome通常画面でH04を選択し、同一候補のPNG/SVG SHA一致を確認済み。隔離ブラウザのSW世代rollbackとWorker停止時のHTTP 502案内・自動復帰・再試行もreadback済み。本番private HTTPS上の世代rollbackと実機iPhoneの同一receipt受入は未確認。
3. 本番反映後のiPhone Safari/PWAで、選択→変換→PNG/SVG保存、機内モード復帰、障害表示と再試行を所有者が受け入れる。
4. Aの既存署名済みPhase4はH04/H06/H08の各候補SHAでPASSし、同じ候補のPhase5も本番コードで再現PASSした。ただしそのH04/H06 candidate SHAは現行L04 bundleのStage8 SHAと異なるため、同一候補のL04三点セットを作り直して照合する必要がある。既存評価者へレビューを再依頼しない。
5. 六能力observerは未導入。下層衣装・ペア別遮蔽・人物内instanceが欠けており、別人物学習catalog、trainer、checkpointもまだ見つかっていない。既知モデルの部分能力を六能力へ読み替えず、Phase4 PASS候補とは独立したゲートとして解消する。
6. L04 release-bound性能receipt、SW offline/rollback/障害時の実ブラウザ受入、実機iPhone Safari/PWA受入、Drive readbackと最終SHA台帳は未完了。Bの配信完了はAの意味品質承認を代替しない。

## 再起動後の実画面H04 readback（2026-11-24 20:48 JST）

- LocalWorker再起動後の所有者専用private HTTPS通常画面で、固定H04入力（source SHA `7d5a6225…`、453×1400）を再変換した。画面は`ZeroBase2 BESTで処理が完了しました。`を表示し、同じ結果からPNGとSVGの保存操作も完了した。
- Downloadsに保存された最新ファイルのSHAはPNG `dc5467db8fdce139ad76cc88e3087e68037070d675cb7ea72180f51901167358`、SVG `feda80bb7405aa6758a839bf2bbef6147b64620d5a20b31c0d9ee7f694d627f4`。採用manifestのH04値と双方一致。
- この確認時のWorker listener PIDは`17264`、supervisor PIDは`38552`、loopback healthは`ready`、runtime errorなし。runtime commit `64cfeb76…`、receipt `381b0b5a…`、manifest SHA `f9ab8fd7…`を結合したsource-free receiptは[LOCAL_L07_GUI_H04_RESTARTED_WORKER_20261124.json](evidence/LOCAL_L07_GUI_H04_RESTARTED_WORKER_20261124.json)。
- このreadbackは再起動後のPCブラウザーでH04通常入口から同一PNG/SVG成果物が保存できることを示す。H06/H08の画面操作、iPhone受入、Aの意味品質、L06性能合格は示さない。

## 現行private HTTPS Originの再読戻し（2026-11-24 13:38 UTC）

- Worker起動設定に保存された所有者専用private HTTPS Originを使い、`/`、`/health`、`/sw.js`、`/manifest.webmanifest`、`/local-static/local-route.js`を再取得した。すべてHTTP 200、healthはready、SWとLocal routeはgeneration `minimalizer-local-20261124-1`。Origin値そのものは公開台帳へ記載していない。
- Worker runtime base `64cfeb76…`はmain `0673449a…`の祖先で、実行中Worker PID `28344`は適用済みコードファイルの更新後に起動。稼働に関係する5ファイルのGit blob SHAは現在のmainと一致し、HTTPSから返る`sw.js`、`local-route.js`、`app.js`の本文SHAもローカルの適用済みファイルと完全一致した。これにより、dirtyな古いruntime checkoutのbase SHAだけでなく、実際に配信されるコードをGitHub mainへ結び付けた。
- 同じOriginを付けた`OPTIONS /api/v2/minimalize`はHTTP 200、CORS Origin echo一致、許可method `GET, POST, OPTIONS`、header `content-type`を確認。
- source-free receiptは[evidence/LOCAL_L07_PRIVATE_HTTPS_ORIGIN_READBACK_20261124T1338Z.json](evidence/LOCAL_L07_PRIVATE_HTTPS_ORIGIN_READBACK_20261124T1338Z.json)。候補receipt `381b0b5a…`、Worker `64cfeb76…`、manifest `f9ab8fd7…`へ結合。
- これはHTTPS配信・Origin/CORS・現行SW世代のreadbackであり、実機iPhone受入または本番HTTPS上の世代rollbackを主張しない。
