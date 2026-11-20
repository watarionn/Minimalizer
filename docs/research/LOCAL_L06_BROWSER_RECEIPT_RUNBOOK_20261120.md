# L06 現行候補ブラウザreceipt手順

## 現在の観測

現行Worker `64cfeb76e5f8ff4e93b6810880c68f1996348ede` の通常入口で、採用候補
`381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` に対応するH04を実測した。
PNG応答はHTTP 200、入力SHA結合、画面表示ともPASSだった。一方、応答ヘッダが
`x-minimalizer-l04-svg-available=true`なのに、配信中の共有 `web/static/app.js` が古く、
SVG保存ボタンを隠していた。このためL06ブラウザreceiptはHOLDであり、APIのPASSだけで昇格しない。

## 修正

共有 `web/static/app.js` を含む5ファイル束を作成した。Service Worker世代は既存の
`minimalizer-local-20261117-2`を維持する。stagingは次の場所にある。

`C:\Work\Temp\minimalizer-l07-runtime-staging-20261120-v6`

manifestの `source_commit` は `086394f01c47726e0675d1c37cf621e63010ec2f`。
この束は本番を変更せず、owner applyと再起動/readbackが必要である。

## owner PCでの反映

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
set "BUNDLE=C:\Work\Temp\minimalizer-l07-runtime-staging-20261120-v6"
set "TARGET=C:\Work\Projects\_runtime\minimalizer-production"
set "BACKUP=C:\Work\Temp\L07_RUNTIME_BACKUP_20261120-v5"
python tools\research\apply_local_l07_runtime_bundle.py --bundle "%BUNDLE%" --target "%TARGET%" --backup "%BACKUP%" --owner-approved
if errorlevel 1 (echo L07_APPLY_HOLD & exit /b 2)
type "%BACKUP%\runtime-apply-manifest.json"
```

既存の所有者承認済み方法でLocalWorkerを再起動した後、既存のruntime readback手順を実行する。
readbackがPASSになるまで、L07/L06をPASSへ変更しない。

## 再測定

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
set "OUT=C:\Work\Temp\minimalizer-l06-current-rerun-20261120\L06_BROWSER_PERFORMANCE_CURRENT.json"
python tools\research\run_local_l06_browser_performance.py --url "https://ywshtmr.tail8fd68c.ts.net:28765/" --case "H04=C:\Work\Temp\minimalizer-l04-production-bundle-20261117\H04\source.png" --case "H06=C:\Work\Temp\minimalizer-l04-production-bundle-20261117\H06\source.webp" --case "H08=C:\Work\Temp\minimalizer-l04-production-bundle-20261117\H08\source.webp" --output "%OUT%" --timeout-seconds 900
type "%OUT%"
```

このrunnerは通常入口でPNG表示とSVG保存を実行し、receiptへは候補SHA、入力SHA、ヘッダ、時間、
ダウンロード成果物のSHA/サイズだけを書き、画像本体・SVG本体・スクリーンショットは保存しない。
3例すべての `browser_render_pass=true` と `performance_pass=true` を確認してから、既存の
`bind_local_l06_regression_candidate.py`へ渡す。L06のPASSはrelease許可を意味しない。
