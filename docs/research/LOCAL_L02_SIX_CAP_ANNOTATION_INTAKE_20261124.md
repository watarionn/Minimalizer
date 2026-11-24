# L02 六能力observer用・新規人物ラベル入力 2026-11-24

## この工程で用意したもの

署名済みH04/H06/H08は評価用のまま固定し、observer学習には使わない。新しい人物データだけを、人が画面でラベル付けして受け入れる入口を追加した。

- ラベル画面: `tools/research/local_l02_six_cap_labeler/index.html`
- 日本語手順: `tools/research/local_l02_six_cap_labeler/README.md`
- 入力監査: `tools/research/verify_local_l02_six_cap_dataset.py`
- 非公開owner mask生成: `tools/research/rasterize_local_l02_six_cap_annotations.py`
- 回帰: `tests/test_local_l02_six_cap_dataset.py`
- Commit: `6e762c8b5aeeaf58df147e6a17384bd3ff095ca0`
- Draft PR: #473, `codex/l02-six-cap-labeler-20261124`

対象能力は、外衣、下層衣装、解剖学的左右の袖、解剖学的左右の腕、人物instance、ペア別遮蔽。画像はブラウザ内で開き、ラベルJSONに画像を埋め込まない。人物グループID、担当者ID、座標、原画像は非公開データとして扱う。

## 検証結果

- 新規画像とラベルJSONのSHA・寸法・座標系一致: 監査器で確認
- H04/H06/H08評価元SHAの学習入力拒否: 実装済み
- 異常ポリゴン、重複ID、未知role、欠落object参照、重複原画像: 拒否
- 未描画画素: unknownを維持。`complete_for` に明示されたroleだけ全画面確認済み陰性になり得る
- 監査出力: 集計件数とbundle fingerprintだけ。画像名・人物/担当者ID・座標は出さない
- 非公開mask生成: source alpha、人物instance map、六つの排他的owner、known/unknownを生成。人物外ラベル・owner重複・Git作業ツリー内出力を拒否
- 回帰: `python -m unittest tests.test_local_l02_six_cap_dataset -v` — 10 PASS（unknown保持、exclusive owner、拒否ケース、非公開出力）
- JS構文: `node --check` — PASS
- Python構文: `py_compile` — PASS
- 送信系Web API: HTML内に `fetch`、`XMLHttpRequest`、`WebSocket`、`sendBeacon` なし
- 実画像P0/P1改善件数: 0件。新規学習画像がまだ入力されていないため、画像品質は未評価
- ローカル画面の実ブラウザ操作確認: 未実施。Codexブラウザの安全ポリシーが `file://` を拒否した。回避操作はしていない

このPASSは入力形式検査と合成入力によるマスク生成までで、実画像データを処理したものではない。observerの学習・精度・owner意味・Phase4/5・Golden・Productionを承認しない。

## 次に必要な作業

### 所有者または指定ラベル担当者

1. H04/H06/H08以外の新しい人物・キャラクターの原画像を、別人物グループで用意する。三つ以上のグループがあれば、訓練・検証・未見人物の分離が可能になる。これは最低限の分割可能性であり、十分な学習量を保証する件数ではない。上限件数は決めず、後の人物単位ホールドアウト結果から追加量を決める。
2. ローカルラベル画面で、各画像の人物instance、外衣、下層衣装、左右袖、左右腕、見える遮蔽ペアを記録する。全画面確認していないクラスはチェックせず、unknownのままにする。
3. 元画像と対応するJSONを非公開Driveの研究データ場所へ保存する。GitHubへ画像・マスク・座標・JSONを置かない。
4. 研究PC上のコピーに入力監査を実行する。監査結果はsource-freeの集計だけをGitHubへ記録できる。

### 開発側（入力受領後）

1. 実データを受領したら監査と非公開マスク生成を行い、人物グループ単位でtrain/validation/blind-testを固定する。
2. 学習前に全六能力の教師信号、排他的可視owner、4/8連結、穴、遮蔽矛盾、未知画素の扱いを検査する。学習・推論へH04/H06/H08の評価ラベルは渡さない。
3. モデルと設定を凍結し、署名済みH04/H06/H08へ同一設定で新規推論する。独立Phase4が評価した後にだけ結果を開き、意味品質と正衣装保持/誤owner除去を確認する。
4. 未見人物testとPhase4の具体的FAILだけを直す。PASS後にPhase5と後続L04/L06/実機ゲートへ進む。

## 残ゲート

L02 HOLD / Phase4 FAIL / Production NO_GO。source-bound private rasterizerまでは用意済み。残る次の具体的工程は、新規人物ラベルを非公開で受領して人物群分割・構造検査を通し、六出力を学習すること。データがない間はモデルを作ったと主張しない。
