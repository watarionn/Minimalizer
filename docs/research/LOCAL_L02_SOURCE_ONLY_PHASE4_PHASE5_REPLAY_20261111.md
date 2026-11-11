# MinimalizerLocal L02 source-only Phase4/Phase5 replay（2026-11-11）

## 目的

現行候補の意味ownerをL04へ昇格させる前に、署名済み元画像だけから作った
ZeroBase Phase4部位分解が、Phase5構造グラフを通過するかを確認した。
この記録はsource-freeであり、原画像・マスク・NPZは非公開の一時成果へ保存する。

## 実行条件

- 入力: H04/H06/H08の署名済み元画像
- Phase3: source alphaのみ。3件ともsource SHA一致
- Phase4: rtmlib `0.0.16`、CPU、balanced、MediaPipe意味ヒントなし
- 人手ラベル・レビューJSON・評価マスク: 推論入力に未使用
- private出力: `C:\Work\Temp\minimalizer-l02-source-phase4-20261111\artifacts`

## 結果

| case | Phase4 | Phase5 | anchors | relations | 構造結果 |
|---|---:|---:|---:|---:|---|
| H04 | 生成完了 | FAIL | 19 | 12 | `neck-attached-to-torso` 欠落 |
| H06 | 生成完了 | PASS | 24 | 15 | isolated major parts なし、arm attachment欠落なし、cycle 0 |
| H08 | 生成完了 | PASS | 24 | 15 | isolated major parts なし、arm attachment欠落なし、cycle 0 |

### source SHA

- H04: `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3`
- H06: `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8`
- H08: `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`

## 成果SHA

| case | Phase4 stage.json | Phase5 metrics.json | Phase5 graph |
|---|---|---|---|
| H04 | `21bf06470cd9920de825e3315361e73f65fc0cddcc26f04a524dd53aa1c0bdc2` | `9f0ac771d6d4a9d3319da7aebd5d90b06fa1a0eb28126efabf8320bf5d8aef9d` | `7b67388cb5e922fd7fe702aa3f42785a1f05aabcdd25f15552b7043eca478c4a` |
| H06 | `a437b5ebdc4a88342a3548567b1e4e115fb3c14e59cfc37510f385a03c90c751` | `a7f7c357710d48acd798b1dc738ca77dc0c04dcdc4f6afd1f74b7c3f7e37d5ea` | `9737ca52261f37f80c38e05d31af80b4bd41f89da8db47e3d8d93892dd2b7289` |
| H08 | `5132b5e705bc3566d00abd783654cf7bd49f06d82fc8b43b3afce82a963f5c3f` | `a7f7c357710d48acd798b1dc738ca77dc0c04dcdc4f6afd1f74b7c3f7e37d5ea` | `f8580f1ca968d3958e5d393ff8e06830f7361b1bded782f0905522888018b814` |

## ゲート判断

これは現行Sapiens2 owner候補のPhase5 PASSではない。source-only部位分解の構造診断であり、
現行候補の`candidate_owner`はこのPhase4部位マスクへ組み込んでいない。
したがって、現行候補bound Phase5入力監査は引き続き`HOLD / NO_GO`とする。

次の実装対象は、意味付けを推測して単純ORすることではなく、candidate SHAを実際に入力へ
結び付けたsource-only Phase4 bundleを生成し、H04の首-胴体接続を含むPhase5を再実行すること。
