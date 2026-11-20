# L02 6能力observer導入計画

## 判定

`ADOPTION_PLAN_PASS_RESEARCH_ONLY`。これは、既存の公開モデルを6能力observerとして昇格させた記録ではない。現時点では、実画像へ適用済みの候補は `CAPABILITY_HOLD_RESEARCH_ONLY` のままなので、Phase4・Phase5・本番権限は付与しない。

## 固定する6能力

実装上は、次の8出力能力を6つの意味領域として扱う。

- 外衣 (`outerwear`)
- 下層衣装 (`underlayer`)
- 袖 (`sleeve`)
- 腕 (`arm`)
- 外衣と下層衣装の遮蔽関係 (`occlusion_outerwear_underlayer`)
- 袖と腕の遮蔽関係 (`occlusion_sleeve_arm`)
- 衣装と身体の遮蔽関係 (`occlusion_garment_body`)
- 人物内instanceのグルーピング (`instance_grouping`)

公開済み24分類モデルのように、外衣・袖・左右腕だけを出力するモデルは、この契約へ別名で埋めない。足りない能力は欠落として記録し、Phase4をHOLDする。

## 導入順序

1. 非公開データのメタデータ台帳を作る。署名済み元画像、注釈、来歴SHAだけを登録し、画像そのものはGitHubへ保存しない。
2. 人物単位でtrain / validation / holdoutを分離する。H04/H06/H08は凍結holdoutとして、学習・閾値調整・推論前のラベル参照から除外する。
3. 6能力全てと `unknown` を別出力できるobserverを学習または導入する。unknownを陰性へ変換しない。
4. H04/H06/H08へ同一設定で新規推論する。人手ラベルは推論入力に渡さず、推論後の評価だけに使う。
5. 推論出力を凍結し、独立Phase4評価でowner排他、遮蔽、4/8連結、穴、重要部位、正衣装保持、誤owner除去を確認する。
6. Phase4が独立PASSした同一候補だけをPhase5へ進める。公開・本番昇格は別の所有者受入を必要とする。

## 既存資材で確認できた部分実績

`C:\Work\Temp\minimalizer-h06-h08-inference-20261109\output\NEW_INFERENCE_RECEIPT.json` には、署名済みH06/H08元画像だけを入力にしたSegFormerの新規推論が記録されている。`SAPIENS2_BODY_PARTS_RECEIPT.json` には、H04/H06/H08に対するsource-onlyの腕・粗い衣装body-parts推論も記録されている。どちらも `human_masks_used_in_inference=false`、`unknown_as_negative=false` である。

ただし、これらを6能力observerの成立とは扱わない。現在確認できるのは外衣、粗い衣装、腕の部分出力までで、下層衣装、袖、3種類の明示的なペア別遮蔽、人物内instanceを同一の正式出力契約として固定したcheckpointは未成立である。従ってG2は「新規推論の実行は確認済み、正式入力昇格はHOLD」とし、G1・Phase4・Phase5を飛び越えない。

## 現在の残作業

この計画を満たす実observer checkpoint、署名済み学習メタデータ、train/validationの別人物データ、6能力を揃えたH04/H06/H08の同一設定推論、独立Phase4 PASSは未完了である。従ってこの計画のPASSは、キャンペーン全体の完了を意味しない。
