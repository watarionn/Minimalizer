# L02 六能力ラベル作成ツール

このツールは、新しい人物データを使ってL02 observerの不足能力を学習・評価するためのラベル作成画面です。画像はブラウザ内で開き、外部へ送信しません。ラベルJSONには画像そのものは入りません。

まずは[START_HERE_ラベル作成.txt](START_HERE_ラベル作成.txt)を読んでください。JSONを手書きせず、画面から作成できます。

## 開き方

1. 非公開Driveの受付フォルダーから「六能力ラベル画面.html」を作業用PCへダウンロードします。Driveのプレビューではなく、ダウンロードしたHTMLをEdgeまたはChromeで開きます。サーバー起動やコマンド入力は不要です。
2. 研究用画像もDrive for desktopで同期するか、一時的に作業用PCへダウンロードします。署名済みH04/H06/H08の評価画像は選ばないでください。
3. 画像を1枚選び、「人物・キャラクターの分割ID」を入力します。同じ人物・同じキャラクターの画像には、毎回同じIDを使います。
4. 右側の画像上をクリックして輪郭を置き、「領域を確定」を押します。領域が離れていても同じ物体なら同じ物体IDを使えます。
5. 人物instance、外衣、下層衣装、左右の袖、左右の腕を、それぞれ見えている範囲だけ描きます。左右は画像上の左右ではなく、人物自身の解剖学的な左右です。遮蔽関係は「手前（隠す側）」と「奥（隠される側）」を選んで追加します。画像上の矢印は手前から奥を示します。
6. そのラベル種類を画像全体で確認し終えた場合だけ「全画面確認」にチェックします。チェックしない種類と描いていない範囲は未知のままです。
7. 「ラベルを保存」を押します。ダウンロードされたJSONを非公開Driveの「02_ラベルJSON」へアップロードします。元画像は「01_元画像」に置きます。画像、マスク、JSONをGitHubへ追加しないでください。

保存を途中で止めた場合は、同じ元画像を再度開いてから保存済みラベルJSONを選ぶと続きから編集できます。元画像のSHA-256または寸法が違うJSONは読み込みを拒否します。

## 入力フォルダーの監査

1. 非公開Driveの「01_元画像」と「02_ラベルJSON」の両方を研究用PCへ同期します。同期された二つのフォルダーを含む親フォルダーを入力にします。元画像1枚につきJSONを1個だけ用意します（画像とJSONは別フォルダーでも構いません）。
2. 作業ツリーのルートでコマンドプロンプトを開き、次を実行します。

```cmd
python tools\research\verify_local_l02_six_cap_dataset.py "C:\path\to\private-six-cap-dataset" --output "C:\path\to\private-six-cap-audit.json"
```

`--output` のJSONには件数とデータ全体のfingerprintだけが入り、元画像名、人物ID、担当者ID、座標は入りません。評価用H04/H06/H08の署名済み画像SHAは拒否されます。この監査PASSは学習適格性や意味品質の承認ではありません。

## 人物単位のデータ分割と非公開学習マスクの生成

監査が六能力・人物グループ・遮蔽ラベルの最低入力条件を満たした後、人物グループ単位のtrain/validation/blind-test分割を固定します。各人物グループは一つのsplitにだけ割り当てられ、blind-testラベルはモデル凍結まで開かない運用にします。source-free summaryには人物IDや画像名が出ませんが、分割manifest自体にはそれらが含まれるため非公開で保存してください。

```cmd
python tools\research\split_local_l02_six_cap_dataset.py "C:\path\to\private-six-cap-dataset" "C:\path\outside-git\private-six-cap-split"
python tools\research\rasterize_local_l02_six_cap_annotations.py "C:\path\to\private-six-cap-dataset" "C:\path\outside-git\private-six-cap-split\person-group-split.private.json" "C:\path\outside-git\private-six-cap-train-validation-masks"
python tools\research\audit_local_l02_owner_mask_bundle.py "C:\path\outside-git\private-six-cap-train-validation-masks" "C:\path\outside-git\private-six-cap-split\person-group-split.private.json"
```

通常のマスク生成はtrain/validationだけを対象にし、blind-testのNPZを出力しません。split integrityを確認するため画像SHAと人物グループの対応は読みますが、blind-testのowner maskは作りません。モデルを凍結し、独立評価者が評価する段階になった後だけ、凍結checkpointファイルを指定して別の空フォルダーへblind-testを生成します。checkpointのSHA-256はツールが計算して記録します。

```cmd
python tools\research\rasterize_local_l02_six_cap_annotations.py "C:\path\to\private-six-cap-dataset" "C:\path\outside-git\private-six-cap-split\person-group-split.private.json" "C:\path\outside-git\private-six-cap-blind-masks" --split blind_test --frozen-model "C:\path\outside-git\private-model\frozen-observer.pt"
```

各NPZにはsource alpha、known範囲つき人物instance map、六つの排他的可視owner mask、意味物体instance map、物体IDに結びついた遮蔽edge、クラスごとのknown mask、source SHA付きメタデータが入ります。`complete_for` で全画面確認した種類だけがsource alpha全域を既知画素とし、それ以外は描画済み陽性部分だけを既知にします。人物外への部位ラベル、複数ownerの画素重複、評価元画像、Git作業ツリー内出力を拒否します。別splitのNPZが残る出力先も拒否するため、splitごとに空の出力先を使ってください。監査・分割・マスク生成のPASSは学習・品質承認を意味しません。

マスク生成後の構造監査は、split manifestとSHA一致、person/object instance番号の連続性、六ownerの排他性、maskから物体instanceへの逆引き、遮蔽edgeの参照先と循環、人物・ownerごとの4/8連結成分数および穴数をsource-free集計で確認します。blind-test maskは監査対象外です。これはラベル構造を検査するだけで、意味ラベルの正しさ、十分な学習量、observer精度を承認しません。

マスクNPZには座標と個別画像由来のデータが含まれるため、非公開領域だけに保存してください。GitHubへ追加しないでください。

## データ分割と推論評価

- `subject_group_id` は、関連画像を訓練・検証・評価にまたがって分割しないための分割グループIDです。単独人物画像は同一人物・キャラクター単位で固定します。複数人物の共同場面は、同じ場面・同じ出演者群の画像すべてに同じIDを使い、各人物は領域ごとの `person_id` で区別します。共同場面の出演者を別画像で単独収録する場合、その画像も同じ分割グループに含めてください。
- H04/H06/H08評価元画像の登録済みSHA-256は読み込みを拒否します。評価画像・評価マスク・推論結果を学習ラベルや推論入力へ混ぜないでください。
- この画面が作るのはアノテーション案です。学習へ入れる前に、重複、人物グループ分割、4/8連結、穴、左右、排他的owner、遮蔽の整合性を独立した検証器で確認してください。
- `complete_for` は、その種類の全画面を人が確認したことだけを示します。未確認を陰性に置き換えるフラグではありません。

## このツールの範囲

このツールはラベル作成だけを行います。observerの学習、モデル選定、閾値調整、推論、Phase4評価、Phase5昇格は行いません。学習に使う人物画像とラベルJSONは非公開の研究保管先で管理してください。
