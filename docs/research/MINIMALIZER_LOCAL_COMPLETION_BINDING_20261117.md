# MinimalizerLocal 完成結合台帳

更新日: 2026-11-17

## 基準

| 項目 | 値 |
|---|---|
| main | `22d36e88c0b9932cd44e209c8d8be4581098dc62` |
| 採用候補receipt | `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` |
| 本番Worker基準 | `64cfeb76e5f8ff4e93b6810880c68f1996348ede` |
| A observer契約・現行台帳 | `05a397f3`（契約実装の基点 `00e9ebb9`） |
| B L07候補 | `6c55ac97605e4b6eb84eedf08b9074fdee417603` |
| B PR | `#465` Draft |

## 今回確認したこと

- L04のH04/H06/H08三点セットは、元画像・Stage8 JSON・展開SVGのSHA照合が3/3で成立。
- 既存の独立評価readbackは、同じ候補SHAに対してL04品質 `PASS`、Golden `PASS`を返す。内部candidate summaryの古いHOLDは、再レビューせずsource-free adapterで分離した。
- Bの三点配信監査は3/3 `PASS`。これはAの意味品質を判定しない。
- Aのsource-free外部入力到着台帳は `05a397f3` に更新され、六能力observer未到着の
  状態を現行B結合へ反映している。
- 現行WorkerへのPC private HTTPSは、PNG成功2経路、415/429/503、入力・出力SHA読戻しを再確認した。iPhoneは現行Workerで未受入。
- L07候補はcache-first、世代固定、クエリ/URLエンコード別名固定、旧世代保持を実装した。
  この台帳のB候補SHAは、独立L04結合readbackまで含む現行PR #465の先端へ更新している。
- 今回のL04/L05/L07/release-bindingテスト66件、実SW Node 3件がPASS。

## 検証範囲の注意

- B変更に関係する選択テスト、実SW、構文検査、差分検査はPASS。
- リポジトリ全体のpytestは、現行の基底環境と隔離QA環境の双方で、既存テストが
  要求する任意依存（`scikit-learn`、`playwright`、`torch`、`fastapi`、
  `scikit-image`等）の未導入によりcollection errorとなった。
- このcollection errorをB実装のPASSや全体回帰PASSへ読み替えない。全体回帰を
  正式PASSへするには、依存を固定したCI/QA環境を別途用意する必要がある。

## 完成結合ゲートの現状

現行のL04/L05/L07証拠をsource-free結合ゲートへ入力した結果は次のとおり。

```text
status: HOLD
release_authorized: false
```

理由:

- L04品質は独立評価readbackでPASSだが、productionは `NO_GO` のまま。
- L05はPC側証拠が揃ったが、iPhone受入を含む正式L05はHOLD。
- L07は静的契約PASSだが、現行Workerでの実機iPhone受入が未確認。
- owner操作・本番反映が未完了。
- 旧L08 readinessは別Worker commitを参照しているため、現行Workerの正式証拠にはしない。

## 残ゲート

1. Aの六能力observerまたは別人物データ学習を成立させる。
2. H04/H06/H08を同一設定でsource-only推論する。
3. 独立Phase4をPASSさせる。
4. H08 owner認可receiptとPhase5 exact replayを同一候補へ結合する。
5. L05/L07 receiptへ候補SHA・Worker SHAを明示結合する。
6. 現行WorkerでiPhone Safari/PWA、PNG/SVG、機内モード復帰、fallback/rollbackを受入する。
7. AのPhase4 PASS後にL04 production/GoldenとPhase5 exact replayを同一候補へ昇格する。
8. owner承認、本番反映、Drive読戻しを完了する。

この台帳は完成宣言ではなく、古い実験・別候補・別Workerの証拠を現行候補へ誤結合しないためのsource-free記録である。
