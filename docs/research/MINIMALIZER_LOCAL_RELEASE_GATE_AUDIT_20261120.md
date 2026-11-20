# MinimalizerLocal 最終ゲート監査

監査基準は候補receipt `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`、本番Worker `64cfeb76e5f8ff4e93b6810880c68f1996348ede`、main `22d36e88c0b9932cd44e209c8d8be4581098dc62`。v5・旧Worker・旧候補は再利用しない。

## 現在の判定

| ゲート | 判定 | 根拠 | 残り |
|---|---|---|---|
| G0 基準固定 | PASS | 候補・Worker・main SHAを固定 | なし |
| G1 6能力observer入力 | HOLD | ローカルに `yolo12138/segformer-b2-human-parse-24` の部分checkpointはあるが、正式capability gateは `outerwear/sleeve/arm` のみPASSで、`underlayer`・3組のpairwise遮蔽・`instance_grouping` が不足。六能力checkpoint/別人物catalogは未到着 | 実observerまたは学習資材 |
| G2 H04/H06/H08新規推論 | HOLD（入力実行は確認済み） | `minimalizer-h06-h08-inference-20261109/output/NEW_INFERENCE_RECEIPT.json` と Sapiens2 body-parts receiptで、署名元画像だけを使った新規推論は確認できる。ただし6能力observerの契約を満たさず、現行候補へのPhase4入力として昇格できない | G1の6能力observer成立後、同一設定で正式実行 |
| G3 独立Phase4 | HOLD | 現行候補に対する意味品質の独立Phase4 receipt未成立 | G2後に一度だけ評価 |
| G4 H08 owner認可 | HOLD | `43d164…`の固定はあるが、G3 PASS後の現行候補receiptへ未結合 | 現行候補向けowner receipt |
| G5 Phase5 exact replay | HOLD | G3/G4待ち | 同一候補で再現 |
| G6 L04三点セット | PASS（B配信範囲） | H04/H06/H08 PNG・SVG実入力3/3 HTTP 200、SVG SHA 3/3一致、candidate receipt/release GO 3/3 | A品質昇格とは分離 |
| G7 L07 runtime | PASS（runtime範囲） | generation-pinned SW、health 200、ZeroBase2認可、rollback経路 | owner shipとは分離 |
| G8 現行Worker iPhone | HOLD | Safari/PWA等の過去回答はあるが、Worker `64cf…`へ結合した現行raw receiptが未読戻し | 現行Workerで再受入 |
| G9 L06回帰・性能 | HOLD（部分PASS） | Approved18=18/18、Approved78=78/78のローカルgateはPASS。別作業領域の再構築summaryにはDiagnostic2 PASS版もあるが、現行receipt SHAを持たず、現行Diagnostic2 summaryはFAILのまま。Approved18→78・Golden・ブラウザ性能をreceipt `381b0b5a…`へ結合したsource-free bindingは未成立 | 現行候補を明示したDiagnostic2 PASSと同一候補binding |
| G10 最終release gate | HOLD | A、G8、G9が未完了 | 全receipt結合 |
| G11 owner ship・保存 | HOLD | `release_authorized`を全体ゲートで確認できていない | owner反映・Drive読戻し |

## B実入力E2Eの確定値

`LOCAL_L04_RUNTIME_E2E_AUDIT_20261120.md` と `audit_local_l04_runtime_e2e.py` のsource-free監査で、H04/H06/H08についてPNG・正式SVGのHTTP 200、入力source SHA、SVG SHA、candidate receipt、case、release GO、MIMEを確認済み。WebP MIME未指定415も再現し、`image/webp`指定でPASSした。

## 2026-11-20 追加照合

非公開DriveのMinimalizer研究フォルダを再読戻しした。L02 CandidateBoundはv1/v2、SourceOnlyは既存zipのみで、六能力checkpoint、別人物train/validation catalog、trainer実体、または現行候補 `381b0b5a…` に結合したL06 Phase14/browser-performance receiptは追加されていない。ローカル保管のCandidateBound v3/v4/v5/v6/v8も旧候補SHAを繰り返すだけで、H08固定対象 `43d164…`への現行候補結合はない。v5は履歴専用として採用対象外を維持する。部分checkpointのH04/H06/H08 source-only実行は能力監査に留まり、正式probeへは昇格していない。この照合により、既存PASS要約を現行候補へ遡及結合せず、G1/G3/G9をHOLDのまま保護する。

## 完了宣言の条件

この表のHOLDを、L04の配信PASSや既存iPhone回答で埋めてはならない。G1→G2→G3→G4→G5を完了し、現行Worker `64cf…`のG8、現行候補のG9、非公開Drive読戻しを揃えた後にだけG10を実行する。G10が `release_authorized=true` にならない限り、Draft解除・正式merge・本番完了宣言は行わない。
