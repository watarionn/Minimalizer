# L02開発方式のリセット: 微小画素パッチからowner再構成へ

更新日: 2026-11-10

## 決定

H06の4画素除去、H08の591画素回復のような凍結ownerへの微小パッチを、
「品質改善」として繰り返さない。これらは安全性確認用のshadow診断として保存するが、
正式Phase4候補・P0/P1改善・完成条件には使わない。

## なぜ方式を変えるか

現在のpost-freeze評価が示す残差は、数画素修正の規模ではない。

| case | 現候補の変更 | なお残る診断残差 |
|---|---:|---:|
| H06 | 4画素除去 | known-negative owner `11,547px`、unknown predicted `80,766px` |
| H08 | 591画素回復 | known-positive未回復 `59,444px`、unknown predicted `3,814px` |
| H04 | 0画素変更 | known-negative owner `4,423px` |

この差は、局所的な誤画素の除去ではなく、衣装・腕・下着・遮蔽のowner境界を
画像全体で再構成できていないことを示す。小さな差分を人間に見せても、レビュー者が
改善の意味を判定できない。

## 新しいAの実装単位

```text
署名済み原画像
   │
   ├─ source-only observer群（独立モデル・SHA固定）
   │       └─ garment / arm / underlayer / occlusion の候補全体
   │
   ├─ coherent component単位のowner再構成
   │       ├─ 既存ownerへの微小追加ではなく、領域全体を再評価
   │       ├─ 排他的owner、4/8連結、穴、source alphaを同時に検査
   │       └─ 根拠が一致しない画素はunknownのまま保持
   │
   └─ 凍結 → full-image / magnified semantic review → Phase4
```

### 2026-11-10 実装済みの土台

`tools/research/local_l02_source_owner_reconstruction.py` を追加した。この段階は
owner番号を生成するものではなく、署名済み原画像とSHA固定済みSapiens2 class map
だけから、画像全体の `upper_clothing`、`lower_clothing`、`garment`、`arm`、
`unknown` を排他的に再構成する観測層である。

- H06: garment 542,016px、43個の8連結成分、arm 4,686px、unknown 56,167px
- H08: garment 394,027px、41個の8連結成分、arm 10,236px、unknown 132,596px
- source SHA と class-map SHA を実行時に照合し、透明画素を候補に含めない
- 既存owner、評価マスク、レビューJSONはAPI入力に存在しない
- unknown は陰性に変換せず、owner番号への割当は
  `ABSTAIN_UNTIL_INDEPENDENT_OWNER_AUTHORITY` として停止する

これは数画素修正の置き換えとなる全身観測の実装であり、まだPhase4候補ではない。
次の大きな実装単位は、この成分集合を袖・腕・下着・正衣装・遮蔽の意味領域へ
独立観測で割り当てるowner-authority層である。根拠が一致しない成分は成分全体を
unknownへ退避し、既存ownerの一部だけを削る処理には戻さない。

### 実装ルール

1. 人手マスク・レビューJSONは推論入力に渡さない。推論後の評価だけに使う。
2. Run30 ownerを少数画素ずつ削るのではなく、source-only observerから全owner候補を
   再計算する。旧ownerは比較用のbaselineとしてのみ読む。
3. 1つのconnected componentを腕・衣装・下着のどれにするか決められない場合、
   画素を散発的に移動せず、component全体をunknownへ退避する。
4. class11一律保護、class32 OR/AND、既知例への閾値後合わせは禁止する。
5. 「変更画素数」ではなく、衣装・袖・腕などの意味領域が一貫して回復／除去され、
   誤ownerがまとまって減ったことを評価する。
6. 変更領域が通常倍率で判定できない候補は、Phase4へ送らず
   `MICRO_DELTA_ONLY` として棄却する。これは品質FAILではなく、開発成果なしの判定である。

## 次の実行順

### H06

H06の11,547pxのknown-negative owner残差を、腕・下着・衣装のcomponent境界として
再分類する。4画素候補はbaseline比較へ戻し、採用しない。

### H08

H08の59,444pxの未回復領域を、袖全体・腕との接触・遮蔽順序を含めて再構成する。
591px回復候補は小規模shadowとして保存し、正式候補にはしない。

### H04

H04は0画素変更のため、H06/H08の方式を先に固定してから、同じ全体owner再構成を
source-onlyで実行する。H04固有の人手ラベルや閾値を移植しない。

## レビュー方式の変更

次回の人間レビューは、通常倍率のbefore/after一枚だけにしない。

- 全体画像
- 変更領域の拡大表示
- owner色を分けたbefore/after
- 腕・袖・下着・遮蔽の意味コメント

を同じ候補SHAに束縛する。「差分が小さすぎる」は品質FAILではなく、
候補を作り直す指示として記録する。

## Bへの影響

BのL04/L05/L07実装、Service Worker世代、cap方針、production runtimeは変更しない。
Aがcoherent owner再構成とPhase4を通過するまで、Phase5・Stage8・L04 handoffは開始しない。

現状は `L02=HOLD / Phase4=FAIL / Phase5=NO_GO / Golden=HOLD / production=NO_GO`。

