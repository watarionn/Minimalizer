# 現行Worker L04実入力E2E監査

## 判定

`minimalizer/local-l04/runtime-e2e-audit/v1` は `PASS`。これは現行Workerの通常APIへ実際の署名済み元画像を送った結果を、source-freeなハッシュ・header監査へ変換した記録である。元画像、PNG、SVG本体は非公開一時領域に残し、GitHubへ保存していない。

- candidate receipt: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- production Worker commit: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- runtime generation: `minimalizer-local-20261117-2`
- health: HTTP 200、`zerobase2_authorized=true`、`runtime_error=null`
- L04 audit tests: 20 PASS

## 実測結果

| case | source SHA | PNG SHA | SVG SHA | PNG処理時間(ms) | SVG三点照合 | HTTP |
|---|---|---|---|---:|---|---|
| H04 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | `b0b2717588ce8e01f4c95609bbe139dd161670b74da1898b6c359891d8d9567a` | `feda80bb7405aa6758a839bf2bbef6147b64620d5a20b31c0d9ee7f694d627f4` | 75444.6 | manifest一致 / receipt一致 / release GO | PNG・SVGとも200 |
| H06 | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `8f5c67193c62b19c4f48083ff810aad41903cfe744ea4ae0b53e43d57c785694` | `1493d7dbeecce0563baa0bb86bcb4230d01f10db14a4a69919d11b841a41ea16` | 322598.4 | manifest一致 / receipt一致 / release GO | PNG・SVGとも200 |
| H08 | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `118a5271c2a24cd26d95c8e7989467c469ecf1f2557729738ba66749299e8ae8` | `712337aa48bdfad3bbda778b903478bc1b4cec1d42e110c95d249b8f82a4860c` | 254811.6 | manifest一致 / receipt一致 / release GO | PNG・SVGとも200 |

全例でPNG headerの入力SHA、SVG headerのcase・candidate receipt・release GO、SVG body SHA、MIMEを監査した。PNG経路はSVG利用可能であることも確認した。

## 障害系

H06/H08のWebPをMIME指定なしで送った場合は `415 Unsupported Media Type` となった。`file=@...;type=image/webp` で再送すると両例ともPASSした。これは入力経路の契約を確認する再現済み障害系であり、候補品質FAILではない。

## 境界

この監査はL04配信・現行Worker実入力・PNG/SVG出力の証拠であり、Aの意味品質、独立Phase4、Phase5、L06 Golden、ownerの正式shipを代替しない。従って本番全体の `release_authorized` は変更せず、A/B最終結合はHOLDのままとする。
