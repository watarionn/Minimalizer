# L02 observer 受入チェックリスト

これは新しい評価結果やreceiptではなく、Aを再開するために必要な入力を人間が確認するための用紙である。画像・マスク・NPZ・秘密情報をGitHubへ貼らない。

## 受け入れるもの

次のいずれか一つを、凛夏または学習担当者から受け取る。

### 実行可能checkpointが既にある場合

- checkpoint本体の非公開保管場所
- checkpointのSHA-256
- 実行コードのcommitまたはrelease SHA
- class mapと出力schemaの版
- 入力画像の前処理、解像度、device、推論設定
- H04/H06/H08を同じ設定で処理できる実行手順
- そのcheckpointが次の六能力を出力できる説明

  1. outerwear（正衣装）
  2. underlayer（下着・下層）
  3. sleeve（袖）
  4. arm（腕）
  5. pairwise occlusion（外衣/下層、袖/腕、衣装/身体）
  6. instance grouping（人物内の個体識別）

### 学習・導入から始める場合

- 学習データの非公開保管場所とdataset revision
- データのcharacter単位のtrain / validation / holdout分割
- 各画像・注釈・重みのSHA-256
- 必須注釈の役割
  `person_instance`、`outerwear`、`underlayer`、`sleeve`、`arm`、
  `occlusion_outerwear_underlayer`、`occlusion_sleeve_arm`、
  `occlusion_garment_body`、`unknown`
- unknownをnegativeへ変換しないことの確認
- H04/H06/H08を学習、閾値決定、早期停止に使わないことの確認
- 学習後に固定するcheckpoint SHA、class map、推論設定、出力schema

## 受け取らないもの

- H04/H06/H08の人手マスクを推論入力へ貼り付けた候補
- H04だけで決めた閾値や、H06/H08だけに合わせたcase別設定
- class11の一律保護、class32の単純OR/AND
- outerwearを`topwear`へ言い換えただけの出力
- depth一枚、連結成分、arm-vetoだけで遮蔽やinstance groupingを代用した出力
- 差分が大きいことだけを根拠にした候補
- ライセンスや評価者の説明だけで、実行コード・重み・出力契約が確認できないもの

## 受け取り後に私が行う順序

1. 非公開保管先からcheckpoint／manifestを読み戻し、SHAを再計算する。
2. 画像や人手ラベルを推論入力へ渡さず、コードと設定だけで能力契約を検証する。
3. H04/H06/H08を同一revision・同一設定で一括推論する。
4. RGB/alpha、source SHA、unknown、4/8連結、穴、遮蔽、exclusive owner、正衣装保持を検証する。
5. 六能力が三例すべてで成立した場合だけ、独立Phase4へ候補を渡す。
6. Phase4が三例PASSした後だけ、Phase5、H08 owner認可receipt、L04三点セットへ進む。

## 現在の記入状況

- 実行可能な六能力checkpoint: **未受領**
- 学習データ／注釈／revision: **未受領**
- Aの判定: `L02 HOLD / Phase4 FAIL / Phase5 NO_GO`
- Bの判定: 実装・統合QA完了記録を維持。Aの品質合否は判定しない。
