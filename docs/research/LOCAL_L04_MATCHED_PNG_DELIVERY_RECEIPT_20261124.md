# Local L04 PNG/SVG同一候補配信記録

作成日: 2026-11-24  
状態: `MERGED_AND_LIVE / PC_NORMAL_FLOW_PASS / IPHONE_AND_OFFLINE_ACCEPTANCE_PENDING`

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

## 残ゲートと次の変更

1. L06 Golden/Approved18→78のevidenceをrelease `191f93d8`とreceipt `381b0b5a…`へ結ぶsource-free bindingを作る。新PNG経路の正式性能receiptを記録し、旧推論経路のHOLDを明確に分離する。
2. PCのcurrent SW offline shell、worker再接続、障害表示・retry・fallback、rollbackの実ブラウザ受入を行う。
3. 本番反映後のiPhone Safari/PWAで、選択→変換→PNG/SVG保存、機内モード復帰、障害表示と再試行を所有者が受け入れる。
4. Aでは現行公開checkpointのH04/H06/H08 source-only出力が六能力中3能力に留まる。六能力checkpointまたは別人物データ・trainerが必要で、独立Phase4はFAIL、Phase5はNO_GOのまま。
5. 所有者は既存署名済みblind評価を再利用する。所有者確認では、未見データ・推論前ラベル非参照・評価者独立・4項目の意味評価は全てYES。レビューの再依頼はしない。残るのは同じ署名済み結果を現在の凍結候補/receipt SHAへ結ぶsource-free receiptである。
6. A Phase4 PASS後だけ同じ候補のPhase5を再現し、Golden・本番・L08受入を結合する。Bの配信完了はAの意味品質承認を代替しない。
