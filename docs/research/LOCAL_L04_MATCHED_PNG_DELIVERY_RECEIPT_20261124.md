# Local L04 PNG/SVG同一候補配信記録

作成日: 2026-11-24  
状態: `MERGED_AND_LIVE / PC_NORMAL_FLOW_PASS / A_PHASE4_PHASE5_REPLAY_PASS / IPHONE_AND_OFFLINE_ACCEPTANCE_PENDING`

## 固定対象

- 候補receipt SHA-256: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- 実機Worker基準commit: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- 実装PR: `#467`（merged）
- 実装main commit: `191f93d85e248f02003ac9835e58484a6d5c177f`
- private bundle ZIP SHA-256: `c489fb5b11c209c491faf5c6aa1d4bdd20652e9f26efad56f4ee871e9a671efe`
- Drive読み戻し: ZIPのサイズ`964667` bytes、SHA-256がローカル値と一致

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
- 実PC Chrome通常画面で署名済みH04を選択し、変換、プレビュー、PNG・SVG保存メッセージを確認。保存ファイルはPNG `dc5467db…`、SVG `feda80bb…`でmanifestと一致。
- 不正なtext/plain入力はprivate HTTPS APIでHTTP `415` JSONとなった。通常画面での障害表示・再試行およびworker停止時の再接続/fallbackは未確認。
- L07 Service Workerはgeneration `minimalizer-local-20261124-1`。静的監査`23 passed`、generation一致、cache-first、cache miss時fail-closed、旧generation cache削除なしを確認。Chrome内部診断URLはComputer UseのURL policyで拒否されたため、更新後generationのoffline実機挙動は未確認。
- 既存Approved18回帰は18/18 PASS、Approved78回帰は78件・SHA/determinism MigrationGate PASS。ただし両コーパスreceiptをこのL04 release SHAへ結ぶsource-free bindingは未作成。
- 既存`L06_BROWSER_PERFORMANCE_CURRENT_RUNTIME_HOLD`はreceipt SHA `381b0b5a…`結合済みだが、旧通常推論経路の性能FAIL（H04 22.6秒）でHOLD。上記の新PNG経路は短時間だが、現行L06の正式なrelease-bound性能receiptへ更新していない。
- 画像semantic P0/P1改善数: 0。これは配信整合性の変更であり、Aの意味品質を主張しない。

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

1. L06 Golden/Approved18→78のevidenceをrelease `191f93d8`とreceipt `381b0b5a…`へ結ぶsource-free bindingを作る。新PNG経路の正式性能receiptを記録し、旧推論経路のHOLDを明確に分離する。
2. PCのcurrent SW offline shell、worker再接続、障害表示・retry・fallback、rollbackの実ブラウザ受入を行う。
3. 本番反映後のiPhone Safari/PWAで、選択→変換→PNG/SVG保存、機内モード復帰、障害表示と再試行を所有者が受け入れる。
4. Aの既存署名済みPhase4はH04/H06/H08の各候補SHAでPASSし、同じ候補のPhase5も本番コードで再現PASSした。ただしそのH04/H06 candidate SHAは現行L04 bundleのStage8 SHAと異なるため、同一候補のL04三点セットを作り直して照合する必要がある。既存評価者へレビューを再依頼しない。
5. 六能力observerは未導入。下層衣装・ペア別遮蔽・人物内instanceが欠けており、別人物学習catalog、trainer、checkpointもまだ見つかっていない。既知モデルの部分能力を六能力へ読み替えず、Phase4 PASS候補とは独立したゲートとして解消する。
6. L04 release-bound性能receipt、SW offline/rollback/障害時の実ブラウザ受入、実機iPhone Safari/PWA受入、Drive readbackと最終SHA台帳は未完了。Bの配信完了はAの意味品質承認を代替しない。
