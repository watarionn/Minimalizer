# MinimalizerLocal L07 本番runtime再結合手順

更新日: 2026-11-17

## 目的

本番runtime `64cfeb76e5f8ff4e93b6810880c68f1996348ede` は、現在のsource側契約と異なる
Service Workerを持つ。runtime側のSWは `minimalizer-local-20261107-1` で、activate時に
旧世代cacheを削除するため、現行L07 gateでは `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK`
となる。

source側のgeneration-pinned実装を本番へ反映する前後に、所有者が次を確認する。

- 対象Worker SHAが `64cfeb76…` から意図した新しいrelease SHAへ変わっている
- `sw.js` と `local-route.js` のgenerationが一致する
- `caches.delete`、`skipWaiting`、`clients.claim` がない
- API・画像・成果物をSW cacheへ入れない
- 旧世代を保持し、rollback可能である
- `/health` のHTTP 200、`runtime_error=null`、`zerobase2_authorized=true`
- その後にPC・iPhone Safari・PWAの実受入を行う

## 反映前のcmd確認

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
git rev-parse HEAD
python tools\research\local_l07_pwa_privacy_audit.py . --output C:\Work\Temp\L07_SOURCE_AUDIT.json
node --check local_worker\frontend\sw.js
```

ここで `STATIC_SW_PRIVACY_CONTRACT_PASS` にならない場合は反映しない。

## 所有者による4ファイル反映

staging manifestが `STAGING_READY` で、対象runtimeのHEADが
`64cfeb76e5f8ff4e93b6810880c68f1996348ede` の場合だけ実行する。バックアップ先は
新しい空ディレクトリを指定し、既存の `dist\` は対象にしない。

```cmd
set "BUNDLE=C:\Work\Temp\L07_RUNTIME_STAGING_20261117-v2"
set "TARGET=C:\Work\Projects\_runtime\minimalizer-production"
set "BACKUP=C:\Work\Temp\L07_RUNTIME_BACKUP_20261117-v2"
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
python tools\research\apply_local_l07_runtime_bundle.py --bundle "%BUNDLE%" --target "%TARGET%" --backup "%BACKUP%" --owner-approved
if errorlevel 1 (echo L07_APPLY_HOLD & exit /b 2)
```

出力が `APPLIED_PENDING_OWNER_RESTART_READBACK` でない場合は停止する。このコマンドは
Worker再起動やhealth読み戻しを行わないため、出力JSONとバックアップを保存した後に、
既存の所有者承認済み方法でruntimeを再起動し、下記の反映後確認へ進む。

## 再起動後のruntime/health receipt生成

再起動後にだけ実行する。これは読み取り専用で、4ファイルのSHA、Worker HEAD、SW世代、
正式L04経路、private HTTPS healthを照合し、source-freeのruntime/health JSONを作る。

```cmd
set "RUNTIME_RECEIPT=C:\Work\Temp\L07_RUNTIME_RECEIPT.json"
set "HEALTH_RECEIPT=C:\Work\Temp\L07_HEALTH_RECEIPT.json"
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
python tools\research\audit_local_l07_runtime_readback.py --runtime-root "C:\Work\Projects\_runtime\minimalizer-production" --bundle "C:\Work\Temp\L07_RUNTIME_STAGING_20261117-v2" --health-url "https://ywshtmr.tail8fd68c.ts.net:28765/health" --runtime-output "%RUNTIME_RECEIPT%" --health-output "%HEALTH_RECEIPT%" --owner-action-confirmed --insecure
if errorlevel 1 (echo L07_READBACK_HOLD & exit /b 3)
type "%RUNTIME_RECEIPT%"
type "%HEALTH_RECEIPT%"
```

このreadbackがPASSになるまで、L07 receiptを最終releaseへ結合しない。

## 所有者によるruntime反映後のcmd確認

runtimeの既存未追跡`dist\`は削除・上書きしない。反映方法は既存の所有者承認済み手順だけを使う。

```cmd
cd /d C:\Work\Projects\_runtime\minimalizer-production
git rev-parse HEAD
python C:\Work\Temp\minimalizer-l07-pinned-20261117\tools\research\local_l07_pwa_privacy_audit.py . --output C:\Work\Temp\L07_RUNTIME_AUDIT.json
curl.exe -k -sS https://ywshtmr.tail8fd68c.ts.net:28765/health
```

監査結果が `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK`、generation mismatch、または
healthの非200・`runtime_error`非nullなら、L07をPASSにしない。

## 実機受入

runtime監査がPASSした後にだけ、既存の
`LOCAL_L05_IPHONE_CURRENT_WORKER_RECEIPT_RUNBOOK_20261117.md`を実行する。
Safari/PWA、PNG/SVG、機内モード復帰、429 Retry-After 2、503 fallback、rollbackを
現行Worker SHAへ結び、raw receipt SHAとbinding監査結果を保存する。

この手順は反映そのものを実行せず、owner-onlyの本番操作と実機確認を代替しない。
