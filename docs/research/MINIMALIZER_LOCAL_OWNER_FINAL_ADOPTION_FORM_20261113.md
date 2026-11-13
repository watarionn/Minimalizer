# MinimalizerLocal 現行候補 owner 最終採用確認票

更新日: 2026-11-13

この確認票は、A/B統合キャンペーンの最後に残った本番採用判断だけを扱う。
GitHub上のコード、Bの既存production、Public/C08、Golden原本をこの票から変更してはならない。

## 採用対象

| 項目 | 現行値 |
|---|---|
| A候補三点セット receipt SHA-256 | `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` |
| L08 readiness receipt | [Drive v2](https://drive.google.com/file/d/1DHTkF63MFs0Jyi_cKJaPVcotzG-6jZ_t/view?usp=drivesdk) |
| L08 readiness SHA-256 | `7E9F35FE97D8CC1EFD590E27BB3D436F567BA02B9DCB284BB3B091DBCD9DF33A` |
| B production commit | `c68dc17bdc2bd3b0ba0841b7108177553891913c` |
| v5履歴SHA | `d7faf5905a24a930963d6435d0864b735506112a867a84302efb75c753ed2536`（採用対象外） |

## 採用前の機械監査

- A H04/H06/H08 三点セット: source・Stage8 JSON・展開SVGのSHA/cross-link `PASS`
- A candidate-specific Phase4 / Phase5: `PASS`
- A v12独立視覚レビュー: `PASS`
- A L04 formal / Golden: `PASS`
- B L04 delivery: `PASS`
- B L05 PC private HTTPS E2E: `PASS`
- B L07 static / iPhone・offline・fallback: `PASS`
- release: `NO_GO`（この票のowner操作前）

## ownerが確認すること

次の二点を確認してから、ワタルさんが普段使っている本番反映経路で、上記の現行A候補を採用する。

1. 採用対象が v5履歴SHAではなく、`381b0b5a…` の現行三点セットである。
2. Bの既存production commit `c68dc17…`、LocalWorkerの入口、Public/C08、Golden原本を変更対象に含めない。

採用する場合のowner確認:

```text
[ ] 現行A候補 receipt SHA 381b0b5a… を本番採用する
[ ] v5履歴SHA d7faf590… は採用しない
[ ] B既存production・Public/C08・Golden原本は変更しない
owner: ____________________
日時(JST): ____________________
```

## 反映後readbackで記録するもの

本番反映後、同じ候補に結び付いた証拠として次を保存する。採用前のreadiness `PASS`だけでは、本番反映済みとは扱わない。

- 実際に配信されたproduction commitまたはrelease識別子
- `/health` のHTTP 200とreadiness payload
- PNG出力の実入力・実出力・SHA-256
- SVG出力の実入力・展開結果・SHA-256
- 415 / 429（`Retry-After: 2`） / 503の障害系応答
- 503時のLocal V2 fallback
- PC実機、iPhone Safari、PWA、機内モード往復のreadback
- readback receiptのSHA-256と非公開Drive再読出し

反映後readbackが揃うまで、正式状態は `production=NO_GO` のまま維持する。
