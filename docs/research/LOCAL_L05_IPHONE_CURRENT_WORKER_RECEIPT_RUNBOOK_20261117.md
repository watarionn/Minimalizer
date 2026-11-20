# 現行Worker iPhone受入receipt作成手順

この手順は、実機iPhoneで一度だけ受入を行い、その結果を現行WorkerへSHA結合するためのものです。
旧receiptの書き換え、合成receipt、スクリーンショットだけの代用はしません。

## 受入前の固定値

- 候補receipt SHA: `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`
- 現行Worker SHA: `64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- PR #465: Draft/HOLD。受入だけでmergeや本番反映は行わない。

## iPhoneで行うこと

同じ候補画像を使い、private HTTPSの現行Worker入口で次を記録する。

1. Safariで画像を選択する。
2. ミニマル化を実行し、PNG結果が表示されることを確認する。
3. PNGを保存する。
4. 同じ入口でSVGを保存する。
5. PWAでも1〜4を確認する。
6. 機内モードをONにしてOFFへ戻し、画面復帰と再試行を確認する。
7. 429と`Retry-After: 2`、503の表示、Local V2 fallbackを確認する。
8. 実際の結果を、所有者用の既存receipt作成手順でJSONへ保存する。

receiptの `production_commit` は必ず上記の現行Worker SHAになることを確認する。
画面写真、元画像、PNG、SVGはGitHubへ置かない。raw receiptも非公開作業領域だけに置く。

## Windows cmdでbindingを生成する

raw receiptをPCへコピーした後、cmdで実行する。パスは実際の保存場所へ置き換える。

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
set "RECEIPT=C:\Work\Temp\private\CURRENT_IPHONE_RECEIPT.json"
set "BINDING=C:\Work\Temp\private\CURRENT_IPHONE_BINDING.json"
set "AUDIT=C:\Work\Temp\private\CURRENT_IPHONE_BINDING_AUDIT.json"
python tools\research\prepare_local_l05_iphone_binding.py --receipt "%RECEIPT%" --output "%BINDING%"
if errorlevel 1 (echo BINDING_HOLD & exit /b 2)
python tools\research\audit_local_l05_current_worker_binding.py --receipt "%RECEIPT%" --binding "%BINDING%" --output "%AUDIT%"
if errorlevel 1 (echo AUDIT_HOLD & exit /b 2)
type "%AUDIT%"
```

最終出力が `"status": "PASS"` で、`device` が `iphone` のときだけ、binding JSONとaudit JSONを
非公開Driveへ保存し、クラウドから読戻してSHAを確認する。`IPHONE_WORKER_COMMIT_MISMATCH`、
`IPHONE_*_INCOMPLETE`、`IPHONE_DRIVE_READBACK_REQUIRED` のいずれかならreleaseへ進めず、
receipt自体を修正してから一回だけ再受入する。

## この手順の完了範囲

この手順のPASSはL05 iPhone証拠の結合を示すだけであり、AのPhase4、L04正式三点セット、
Phase5、Golden、owner本番反映を許可しない。全体release gateは、それらが同じ候補SHAへ結合された
後に別途実行する。
