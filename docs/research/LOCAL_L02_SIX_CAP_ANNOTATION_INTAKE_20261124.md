# L02 六能力observer用・新規人物ラベル入力 2026-11-24

## この工程で用意したもの

署名済みH04/H06/H08は評価用のまま固定し、observer学習には使わない。新しい人物データだけを、人が画面でラベル付けして受け入れる入口を追加した。

- ラベル画面: `tools/research/local_l02_six_cap_labeler/index.html`
- 日本語手順: `tools/research/local_l02_six_cap_labeler/README.md`
- 入力監査: `tools/research/verify_local_l02_six_cap_dataset.py`
- 人物群split固定: `tools/research/split_local_l02_six_cap_dataset.py`
- 非公開owner mask生成: `tools/research/rasterize_local_l02_six_cap_annotations.py`
- 回帰: `tests/test_local_l02_six_cap_dataset.py`
- 初回実装Commit: `6e762c8b5aeeaf58df147e6a17384bd3ff095ca0`
- 私有mask生成追加Commit: `505afe184e4810f70cc30d7d0cb5fb94069af0cc`
- Draft PR: #473, `codex/l02-six-cap-labeler-20261124`

対象能力は、外衣、下層衣装、解剖学的左右の袖、解剖学的左右の腕、人物instance、ペア別遮蔽。画像はブラウザ内で開き、ラベルJSONに画像を埋め込まない。人物グループID、担当者ID、座標、原画像は非公開データとして扱う。

## 検証結果

- 新規画像とラベルJSONのSHA・寸法・座標系一致: 監査器で確認
- H04/H06/H08評価元SHAの学習入力拒否: 実装済み
- 異常ポリゴン、重複ID、未知role、欠落object参照、重複原画像: 拒否
- 未描画画素: unknownを維持。`complete_for` に明示されたroleだけ全画面確認済み陰性になり得る
- 監査出力: 集計件数とbundle fingerprintだけ。画像名・人物/担当者ID・座標は出さない
- 非公開mask生成: source alpha、known範囲つき人物instance map、六つの排他的owner、意味物体instance map、物体IDへ結合した遮蔽edge、known/unknownを生成。人物外ラベル・owner重複・Git作業ツリー内出力を拒否
- mask構造監査: `tools/research/audit_local_l02_owner_mask_bundle.py`。train/validationのSHA対応、instance番号、unknown保持、六owner排他、物体mask対応、遮蔽参照・循環、4/8連結と穴数をsource-free集計で確認。blind-test maskは読まない
- 人物単位split: 固定SHA順でtrain/validation/blind-testを割当て。同一人物群の交差なし、blind labelsは凍結まで隔離。manifestはsource/group IDsを含むため非公開保存
- 回帰: `python -m unittest tests.test_local_l02_six_cap_dataset -v` — 11 PASS（unknown保持、exclusive owner、遮蔽edge対応、再現可能group split、train/validationだけの既定raster、凍結checkpointなしのblind拒否、構造監査、4/8連結・穴、遮蔽循環拒否、非公開出力）
- JS構文: `node --check` — PASS
- Python構文: `py_compile` — PASS
- 送信系Web API: HTML内に `fetch`、`XMLHttpRequest`、`WebSocket`、`sendBeacon` なし
- 実画像P0/P1改善件数: 0件。新規学習画像がまだ入力されていないため、画像品質は未評価
- 実ブラウザ表示: PC上のChromeでローカル `index.html` を開き、日本語の画像選択・6能力ラベル・unknown・遮蔽・保存UIを確認。画像選択、JSON保存、ダウンロード実操作は未確認
- 実人物画像のmask構造監査: 未実施。非公開Driveの元画像/JSON受領待ち

このPASSは入力形式検査と合成入力によるsplit/mask生成までで、実画像データを処理したものではない。observerの学習・精度・owner意味・Phase4/5・Golden・Productionを承認しない。既定rasterizerはblind-test maskを出力せず、凍結checkpointファイルを指定する別操作だけがblind-testを展開する。

構造監査は、instance配列と既知/未知マスクの整合、owner排他、遮蔽edgeの循環、4/8連結成分数・穴数を検査する。PASSはannotationの意味的正しさを保証せず、学習・評価・昇格のゲートを置き換えない。

## 次に必要な作業

### 所有者または指定ラベル担当者

1. H04/H06/H08以外の新しい人物・キャラクターの原画像を、別人物グループで用意する。三つ以上のグループがあれば、訓練・検証・未見人物の分離が可能になる。これは最低限の分割可能性であり、十分な学習量を保証する件数ではない。上限件数は決めず、後の人物単位ホールドアウト結果から追加量を決める。
2. ローカルラベル画面で、各画像の人物instance、外衣、下層衣装、左右袖、左右腕、見える遮蔽ペアを記録する。全画面確認していないクラスはチェックせず、unknownのままにする。
3. 元画像と対応するJSONを非公開Driveの研究データ場所へ保存する。GitHubへ画像・マスク・座標・JSONを置かない。
4. 研究PC上のコピーに入力監査を実行する。監査結果はsource-freeの集計だけをGitHubへ記録できる。

### 開発側（入力受領後）

1. 実データを受領したら監査、人物単位split固定、非公開マスク生成を順に行う。
2. 学習前に全六能力の教師信号、排他的可視owner、4/8連結、穴、遮蔽矛盾、未知画素の扱いを検査する。学習・推論へH04/H06/H08の評価ラベルは渡さない。
3. モデルと設定を凍結し、署名済みH04/H06/H08へ同一設定で新規推論する。独立Phase4が評価した後にだけ結果を開き、意味品質と正衣装保持/誤owner除去を確認する。
4. 未見人物testとPhase4の具体的FAILだけを直す。PASS後にPhase5と後続L04/L06/実機ゲートへ進む。

## 残ゲート

L02 HOLD / Phase4 FAIL / Production NO_GO。source-bound private rasterizerまでは用意済み。残る次の具体的工程は、新規人物ラベルを非公開で受領して人物群分割・構造検査を通し、六出力を学習すること。データがない間はモデルを作ったと主張しない。

## 2026-11-24 継続記録

- 構造監査・回帰: commit `96d958d7ebff6af3b65820975c1f7e80fd76dc3c`。合成入力で11/11 PASS。4/8連結、穴、未知保持、instance番号、owner排他、遮蔽循環を検査。意味品質の承認ではない。
- 利用手順: commit `cb550f100d8eb1971156c3ef00471be4cd8565fc`。日本語の短い開始手順を追加し、JSON手書き不要、ローカルHTMLを開くこと、画像をローカルから選ぶこと、DriveへJSONを戻すことを明記。
- Draft PR #473は同ブランチの最新HEADに追随。非公開Drive受付フォルダーにstandalone HTML（19,404 bytes）と開始案内（2,679 bytes）を配置し、案内のDrive読み戻しを確認。原画像・JSON・マスク・座標はまだ未受領。
- 画像品質改善数: P0 0件 / P1 0件。実画像推論・学習を行っていないため。
- 残ゲート: 別人物グループの実画像と画面生成JSONの受領、実画像入力監査、人物group split、train/validation mask構造監査、6能力の学習と凍結、同一設定のH04/H06/H08新規推論、独立Phase4 PASS、Phase5再現。
- 次の具体的作業: データを受領したらsource-free入力監査を実行し、分割可能性と不足するラベル能力を数値で確認する。その結果から学習・検証用データ追加とモデル導入を進める。3人物グループはsplit可能性の最低条件であり、学習十分性の基準にはしない。
