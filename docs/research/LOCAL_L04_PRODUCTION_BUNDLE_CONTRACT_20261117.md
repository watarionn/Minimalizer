# Local L04 production bundle contract

この契約は、独立評価で正式合格した Local L04 の三点セットを、通常の
LocalWorker入口へ渡すための読み取り境界です。候補を作成したり、品質を
合格扱いにしたりする機能ではありません。

## 出荷条件

`tools/research/local_l04_production_bundle.py` は、次の条件をすべて満たす
manifestだけを受け付けます。

- `schema` が `minimalizer/local-l04/production-bundle/v1`
- `candidate_receipt_sha256` が64桁SHA-256で、呼び出し側の固定値と一致
- `L04_formal` と `Golden` が `PASS`
- `production` が `GO`
- `release_authorized` と `source_free_repository_record` が `true`
- H04/H06/H08の3ケースが存在
- 各ケースの署名済み元画像、Stage8 JSON、展開SVGがbundle配下にある
- 3ファイルのSHAがmanifestと一致
- Stage8 JSONの元画像/SVG相互リンクが一致
- SVGが安全な展開形式で、外部参照・スクリプト・埋め込み画像を含まない
- L04の数値ゲートが独立評価へ進める状態

どれか一つでも失敗した場合は `L04ProductionBundleHold` で停止します。
現在の既存候補パッケージは `HOLD` / `NO_GO` のため、このローダーからは
読み出せません。

## manifestの形

```json
{
  "schema": "minimalizer/local-l04/production-bundle/v1",
  "candidate_receipt_sha256": "<receipt sha256>",
  "L04_formal": "PASS",
  "Golden": "PASS",
  "production": "GO",
  "release_authorized": true,
  "source_free_repository_record": true,
  "cases": {
    "H04": {
      "source": {"path": "private/H04.source", "sha256": "<sha256>"},
      "stage8_json": {"path": "private/H04.stage8.json", "sha256": "<sha256>"},
      "expanded_svg": {"path": "private/H04.expanded.svg", "sha256": "<sha256>"}
    },
    "H06": {},
    "H08": {}
  }
}
```

元画像と実体験用の比較画像はリポジトリへ保存しません。private bundleと
非公開Driveの読戻しを確認したうえで、manifestのSHAだけをsource-freeな
台帳へ残します。manifestがPASSになるまで、通常入口へのPNG/SVG経路を
有効化してはいけません。
