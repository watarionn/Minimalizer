# MinimalizerLocal L04 source-route smoke receipt

実施日: 2026-11-17

## 結果

source側の現行B head `89092cae0134036d1786896d00e9f6ff0fac31b2` を一時ポートで起動し、
正式三点セットbundleに含まれるH04署名済み元画像を通常の
`POST /api/zerobase2/minimalize` 入口へ `output_format=svg` で投入した。

| 項目 | 結果 |
|---|---|
| HTTP | `200` |
| mode | `l04-formal-svg` |
| route | `zerobase2` |
| case | `H04` |
| candidate receipt SHA | `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` |
| source SHA-256 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` |
| response SVG SHA-256 | `feda80bb7405aa6758a839bf2bbef6147b64620d5a20b31c0d9ee7f694d627f4` |
| approved expanded SVG SHA-256 | `feda80bb7405aa6758a839bf2bbef6147b64620d5a20b31c0d9ee7f694d627f4` |
| exact output match | `true` |

## 境界

この確認は正式L04 source-routeの実サーバー疎通と三点セットSHA照合を示す。
隔離実行環境では任意依存の `rtmlib` が無く、`/health` は `status=degraded`、
`ready=false` だった。したがって本番runtimeのhealth、PC/iPhone受入、L05/L07、
最終release gateをPASSに昇格させる証拠ではない。

元画像・Stage8 JSON・SVG本体は非公開bundleに保管し、本文にはSHAだけを記録する。
