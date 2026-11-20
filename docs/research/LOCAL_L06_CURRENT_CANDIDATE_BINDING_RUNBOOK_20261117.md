# L06現行候補結合手順

## 目的

Approved18→78、Golden、ブラウザ表示、性能の結果を、採用候補
`381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`へ明示結合する。
旧Phase14 summaryだけでは候補SHAがないため、正式L06へ昇格しない。

## 入力契約

1. Phase14 summaryは `minimalizer/local-l06/phase14-summary/v1` とし、トップレベルに
   現行候補SHAを持つ。
2. Approved18、Approved78、Diagnostic2の各入力SHAと、3ゲートのPASSをsummaryへ記録する。
3. ブラウザ・性能receiptは `minimalizer/local-l06/browser-performance/v1` とし、同じ候補SHA、
   `browser_render_pass=true`、`performance_pass=true`を持つ。
4. binding JSONは、summary本体とbrowser/performance receipt本体のSHAを記録する。
5. 画像、SVG、スクリーンショット、NPZ、private Drive本文はこの監査へ渡さない。

## cmdでの監査

```cmd
cd /d C:\Work\Temp\minimalizer-l07-pinned-20261117
set "SUMMARY=C:\Work\Temp\private\L06_PHASE14_CURRENT.json"
set "BROWSER=C:\Work\Temp\private\L06_BROWSER_PERFORMANCE_CURRENT.json"
set "BINDING=C:\Work\Temp\private\L06_CURRENT_BINDING.json"
set "OUTPUT=C:\Work\Temp\private\L06_CURRENT_REGRESSION_RECEIPT.json"
python tools\research\bind_local_l06_regression_candidate.py --summary "%SUMMARY%" --browser-performance "%BROWSER%" --binding "%BINDING%" --output "%OUTPUT%"
if errorlevel 1 (echo L06_HOLD & exit /b 2)
type "%OUTPUT%"
```

出力が `status=PASS`でも、これはL06 receiptの生成だけであり、releaseを許可しない。
最終gateへ渡す前に、候補SHA、L04、Phase4、Phase5、L05、L07、保存receiptを同じ版へ揃える。

## 現在の旧結果

`minimalizer-approved18-regression-20261117/14_phase_gate_summary.json`はPhase14内部ではPASSだが、
トップレベルの現行候補SHAを持たない。そのためこのadapterでは
`SUMMARY_CANDIDATE_BINDING_MISSING_OR_MISMATCH`となり、現行L06へ流用しない。
