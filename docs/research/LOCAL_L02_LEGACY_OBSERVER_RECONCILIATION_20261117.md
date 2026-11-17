# L02 旧observer成果の現行契約照合

更新日: 2026-11-17

## 結論

非公開作業領域には、H04/H06/H08へsource-onlyで実行した旧observer成果が存在する。
しかし、現行の六能力契約を満たす固定checkpointではない。これらを現行observer、Phase4
候補、owner authority、または本番品質の証拠へ読み替えない。

## メタデータだけで確認した差分

| 旧成果 | 確認できる能力・状態 | 現行契約との差分 | 判定 |
|---|---|---|---|
| DeepFashion raw probe | 外衣の検出、source-only、unknown分離 | 下層衣装、三組の明示的pairwise遮蔽、人物内instanceの統合契約がない | 研究shadowのみ |
| SCHP ATR/LIP | 人体・衣装系の公開class出力、unknown分離 | 外衣/下層衣装/袖/腕を現行のowner契約として同時出力しない | 研究shadowのみ |
| See-through body-part | body-part分類 | 外衣、下層衣装、三組の遮蔽、人物内instanceが出力契約にない | capability HOLD |
| Layered garment solver | 腕との接触に対する衣装候補、unknown保持 | observerではなく後段solver。`underlayer_evidence_available=false`、品質未評価 | Phase4 FAIL |
| Component owner solver | 外衣候補、腕・instance補助、unknown保持 | `underlayer_evidence_available=false`。owner昇格不可 | Phase4 FAIL |
| Independent observer agreement | H06/H08はshadow agreement、H04はempty abstention | agreementはsemantic truthでもowner authorityでもない | owner昇格不可 |

## 保持する証拠

- 旧成果のsource-only実行、入力source SHA、モデルrevision、出力SHAは非公開台帳で保持する。
- 旧成果の `Phase4=FAIL`、`quality=UNASSESSED`、`production=NO_GO` を保持する。
- 旧成果を再推論したり、既存の人手評価を新observerの推論入力へ流用したりしない。

## 現行候補へ進めるための不足入力

次のいずれかが必要である。

1. 六能力を同一revision・同一設定で出力する固定checkpointと重みSHA。
2. 別人物データによるtrain/validation/holdout分離、source署名、annotation SHA、
   9役割・3組遮蔽・instance・unknownを含む学習catalog。

到着後は `audit_local_l02_observer_intake.py` を通し、PASSした場合だけ三例の新規推論、
凍結、独立Phase4へ進む。この記録だけではPhase4・Phase5・本番権限は発生しない。
