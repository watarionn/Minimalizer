# Aレーン外部入力の現行到着状況 — 2026-11-17

## 目的

六能力observerまたは別人物データ学習を成立させるための外部入力について、
到着済みの資材と未到着の資材を固定する。過去のH04/H06/H08評価資材を、
学習入力や新規observerの根拠へ誤用しない。

## 現行確認

- ローカルに `Live2DCubismCore.h`、Windows x64のCore library、
  `Samples/Common` は存在しない。
- ローカルのCubismPartExtr作業コピーには、モデル資材と抽出コードはあるが、
  Cubism Core SDKがないため実行可能な抽出結果を作れていない。
- Google Driveの限定検索（`Cubism SDK`、`CubismPartExtr`、`Live2D`、
  `六能力 observer`、`pairwise occlusion`、`H06 H08`）では、
  新しいSDK、六能力checkpoint、別人物の注釈済み学習catalogは見つからなかった。
- Driveで確認できた `L02_H06_H08_NEW_BLIND_AUDIT_20261108` は既存の
  H06/H08評価用画像・NPZ・結果JSONであり、H04/H06/H08を学習・閾値決定へ
  使用してはならない。

## ローカル資材のメタデータ再確認

2026-11-17に、画像・マスク・NPZ・重みの内容を開かず、ファイル名、receipt JSON、
仕様メタデータ、ファイルSHAだけを再確認した。

- `SAM_BODY_PART_19_CAPABILITY_RECEIPT_20261110.json` は
  `CAPABILITY_HOLD`。H04/H06/H08で確認できたのは `outerwear` と `sleeve`だけで、
  `arm`、`underlayer`、遮蔽関係、`instance_grouping`が欠落し、`phase4=FAIL`、
  `production=NO_GO`である。六能力observerとして採用しない。
- Fashionpedia系checkpoint `checkpoint_best_ema.pth` は存在するが、SHA
  `aafefc440ea8f3f388e894a898e4270a2eeb6e38a3c3ffd3751d07d0f30b26bb`に対応する
  現行observer仕様JSON、固定revision、六能力の個別output contract、三例同一設定の
  source-only receiptがない。候補重みの存在だけではintake PASSにしない。
- 既存の `model.safetensors`（SHA
  `47313d9daf8f759b803b0bf449a4719bcd5b5a46eacad343e99e9660f8cedec1`）と
  Sapiens2 segmentation重み（SHA
  `b85fdb50b7d6123a967d5ee4a505e222baff8d2f7ad6bbf353578c1a61dfbac9`）も、現行の
  六能力・pairwise遮蔽・人物内instance契約を宣言する仕様またはreceiptがないため、
  observer入力として採用しない。

この再確認で「重みファイルがある」と「現行六能力observerが成立している」を分離した。
現在のAは引き続き `TRAINING_INPUT_HOLD` / `CAPABILITY_HOLD` である。

## 未到着の実装入力

次のいずれかが揃うまで、Aのobserver昇格はHOLDとする。

### ルートI: 実行可能checkpoint

- 固定revisionと重みSHA
- 外衣、下層衣装、袖、腕、3組のpairwise遮蔽、人物内instanceの出力
- unknownを陰性へ変換しない出力schema
- 署名済み元画像だけでsource-only推論できる実行手順

### ルートII: 別人物学習入力

- Cubism Core SDKを使った別人物モデルの抽出結果、または同等の別人物データ
- 9役割（6能力、3遮蔽、unknown）のpixel annotation
- source署名、annotation SHA、人物単位のtrain/validation分離
- H04/H06/H08をholdoutにしたtraining manifest

## 次の所有者操作

SDKまたは学習入力が届いたら、非公開作業領域へ置き、次の順で読む。

1. SDK/header/libraryまたはcheckpointのSHAを記録する。
2. `import_live2d_training_catalog.py` とtraining manifestで入力境界を検証する。
3. H04/H06/H08を推論前に開かず、同一設定でsource-only一括推論する。
4. capability gateが六能力、unknown、source境界、人物分離をPASSした場合だけ、
   Phase4用候補を作る。

## source-free intake監査

`tools/research/audit_local_l02_observer_intake.py` を追加した。実行例と到着後の順序は
`LOCAL_L02_OBSERVER_INTAKE_RUNBOOK_20261117.md` に固定した。`checkpoint` 経路は
重みSHA、固定revision、六能力の個別出力契約、unknown分離、三例同一設定を確認する。
`training` 経路はCubism Coreの必要ファイル・ディレクトリと、catalog importerの
別人物train/validation/holdout境界を一括確認する。どちらも画像・マスク・NPZ・レビューを
開かず、PASSしても研究probeだけを許可し、Phase4・Phase5・本番権限は付与しない。

現時点のテストでは、この監査を含むAの関連テストが `89 passed`。実資材の到着判定は
別途この監査を実行して行い、現在の未到着状態をPASSへ読み替えない。

## GitHub再確認（2026-11-17）

GitHubのA系Draft PR #447、#448、#449、#452と、`research/local-l02-*` の現行公開
ブランチ一覧を再確認した。いずれにも、現行契約を満たす実行可能checkpoint、Cubism
SDK、または別人物の六能力training catalogは追加されていない。PR #449に記録された
Phase4/Phase5の記述は旧候補の履歴であり、現行の六能力intake・現行候補SHA・現行
Workerへ結合できないため採用しない。現行Aの正本はこのブランチの
`a21f92f06aadfc0e4110e7bd6125f06fecab1a2f` とする。

この記録はライセンス判定ではなく、Aの実行入力が現時点で未到着であることを
固定するためのsource-free台帳である。
