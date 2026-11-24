# Local L04 PNG/SVG同一候補配信記録

作成日: 2026-11-24  
状態: `CODE_AND_PRIVATE_BUNDLE_READY / LIVE_PWA_ACCEPTANCE_PENDING`

## 固定対象

- 候補receipt SHA-256: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- 実機Worker基準commit: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- 実装PR基準main commit: `22d36e88c0b9932cd44e209c8d8be4581098dc62`
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
- 最新main基点のFocused tests: `60 passed`（LocalWorker、L04 source/Stage8/SVG gate、delivery audit、L07 privacy audit）。
- real private inputsを用いたTestClient E2E: H04/H06/H08のPNG/SVG全6要求がHTTP 200、receipt SHAと各成果物SHAがmanifestに一致。
- Node/Python構文確認: PASS。派生PNG再生成のSHA一致: 3/3。
- Worker private HTTPS: 現在の旧v1 bundleからのH04 SVG取得はHTTP 200、SHA一致を確認。新v2 PNGコードはまだlive Workerへ適用していない。
- L07 Service Worker: generation `minimalizer-local-20261124-1`へ更新。現行世代のcache-first、cache miss時fail-closed、前世代cache保持、activate時の削除なしを静的監査で確認。世代更新後のrollbackと実ブラウザ挙動は未確認。
- 画像semantic P0/P1改善数: 0。これは配信整合性の変更であり、Aの意味品質を主張しない。

## 残ゲートと次の変更

1. このsource-free変更をDraft PR #467へ反映し、`64cfeb76…`の専用runtimeへレビュー後に適用する。
2. v2 private bundleをWorker起動設定へ登録し、通常private HTTPS入口でH04/H06/H08のPNG/SVG SHAを再取得する。
3. PCブラウザの通常画面で選択、PNG表示/保存、SVG保存を確認する。Service Worker世代更新とrollbackを維持する。
4. L06 Golden・Approved18→78回帰・性能の現行候補bound結果を一つのrelease SHAへ結ぶ。iPhone Safari/PWAの本番後受入は別途必要。
5. Aの六能力observerと独立Phase4/Phase5、L08の実機受入は未完了。これらをこの配信記録で代替しない。
