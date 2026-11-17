# L07 runtime binding receipt手順

## 目的

ownerが本番runtimeへ反映した後、runtimeのWorker SHA、Service Worker世代、rollback、
healthを採用候補へ結合する。静的source監査PASSやhealth 200だけではL07 PASSにしない。

## owner反映後に用意するJSON

runtime receiptは `minimalizer/local-l07/runtime/v1` とし、少なくとも次を含める。

- `status=PASS`
- `production_worker_commit=64cfeb76e5f8ff4e93b6810880c68f1996348ede`
- `runtime_sw_audit_pass=true`、`runtime_generation_bound=true`
- generation固定、旧世代保持、rollback可能、API/画像非cache
- `generation` と `source_generation` の一致

health receiptは `minimalizer/local-l07/health/v1` とし、HTTP 200、`status=ready`、
`runtime_error=null`、`zerobase2_authorized=true`を含める。画面写真や画像本体はJSON監査へ渡さない。

## cmd

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
set "RUNTIME=C:\Work\Temp\private\L07_RUNTIME_RECEIPT.json"
set "HEALTH=C:\Work\Temp\private\L07_HEALTH_RECEIPT.json"
set "BINDING=C:\Work\Temp\private\L07_RUNTIME_BINDING.json"
set "OUTPUT=C:\Work\Temp\private\L07_RUNTIME_RELEASE_RECEIPT.json"
python tools\research\bind_local_l07_runtime_release.py --runtime "%RUNTIME%" --health "%HEALTH%" --binding "%BINDING%" --output "%OUTPUT%"
if errorlevel 1 (echo L07_HOLD & exit /b 2)
type "%OUTPUT%"
```

現行runtimeの監査結果が `SW_OLD_GENERATION_DELETION_BREAKS_ROLLBACK` の間は、
このadapterへ渡してもHOLDであり、receiptを手作業でPASSへ書き換えない。

このreceiptのPASSはL07のruntime結合だけを示す。iPhone受入、L04、A Phase4/5、L06、
最終release gate、owner本番完了を代替しない。
