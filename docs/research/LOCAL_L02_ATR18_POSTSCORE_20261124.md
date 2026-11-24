# SCHP-ATR18 H06/H08 後評価（2026-11-24）

## 判定

署名済みH06/H08の元画像に同一設定で実行して凍結したSCHP-ATR18のclass mapを、推論時には読んでいない独立評価マスクと照合した。Drive保存後のNPZ・receipt・manifestはクラウド読戻しでDriveFS実体とSHA-256が一致し、評価アーカイブ内のファイルも内部マニフェストと全件一致した。

今回の数値は「ATR18衣装クラス群」と「人手の衣装/衣装以外ラベル」の広い二値比較である。六能力observer、衣装所有者、袖・下層衣装の判別、Phase4品質の合格を示さない。予測class mapはowner maskへ変換していない。未知・曖昧画素と元画像の透明画素は採点から除外した。

| ケース | Precision | Recall | IoU | 人手衣装4連結成分 | ATR18衣装4連結成分 |
|---|---:|---:|---:|---:|---:|
| H06 | 0.934 | 0.691 | 0.659 | 3 | 37 |
| H08 | 0.789 | 0.937 | 0.749 | 2 | 11 |

主要な失敗は、H06の衣装領域の大きな取りこぼしと過分割、H08の誤衣装領域と過分割。したがってATR18単独ではH06/H08のowner修復を採用できず、袖・下層衣装・ペア別遮蔽・人物instanceを含む六能力要件も満たさない。これは数画素の後処理で救済する対象ではなく、追加observerまたは別人物データを使う学習計画が必要である。

## 再現コードと記録

- 採点器: `tools/research/local_l02_atr18_postscore.py`
- source-free結果: `docs/research/LOCAL_L02_ATR18_POSTSCORE_20261124.json`
- テスト: `tests/test_local_l02_atr18_postscore.py`（6件PASS）
- 固定モデル: SCHP-ATR18 revision `a54fa65e7e4f27f21011f652ffc0053ebb24b292`, SHA-256 `4420d8db8c1f266967c89485786b01209f6d405f320fc0f87e8ced49392cefb5`
- 使用クラス群: ATR18 IDs `4,5,6,7,8,9,10,17`。腕クラス14/15は衣装予測に混ぜず、既知の衣装以外ラベルとの重なりを別に報告する。
- 受入マスクとclass map本体は非公開Driveにのみ保持。GitHubには座標、画像、マスク、NPZを置かない。

## 状態

この工程は後評価の再現コードとsource-free記録を追加した。実画像のP0/P1修正は **0/0**。L02はHOLD、Phase4はFAIL、L03/ProductionはNO_GOのまま。人手ラベルは推論後にのみ読み、未知を陰性化していない。独立Phase4評価、Phase5 replay、Golden、本番昇格は未実施。
