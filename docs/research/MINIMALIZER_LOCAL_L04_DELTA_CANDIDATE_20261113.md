# Minimalizer Local L04 差分候補記録 — 2026-11-13

## 目的

v5候補に対する独立視覚確認を再利用し、候補の実装差分で変わった表示点だけを確認する。v5の回答を別候補へ流用しない。

## receiptの境界

- v5候補receipt SHA-256: `d7faf5905a24a930963d6435d0864b735506112a867a84302efb75c753ed2536`
- v5回答ファイルSHA-256: `f579f1b3cac2cf96ad42690ff70035a0296584f56cff6bd641738f15b3aadf83`
- v5結果: H04は質問3、H06は質問1と6が不合格。H08は全問合格。総合HOLD。
- 現候補receipt SHA-256: `a6c16d3377b805484f94eb57f0346bc3bc9bc2376ce38b795a8e0f4a0a507cb7`

v5回答はv5 receiptに対する正式な回答として保存する。現候補に対しては、v5の不合格3項目とH08の無回帰だけを確認する4問の差分票を使用する。

## 現候補で変えたもの

### A: H06/H08 owner修復

`candidate-positive-garment-preserve-known-v3-outerwear-arm-arbitration` を追加した。

- 人手ラベル、レビューJSON、凍結ownerは推論入力に使用しない。
- 未知画素を陰性扱いしない。
- 8連結の外衣観測componentが腕ownerと衣装contextの両方に接続するときだけ、重なった既存腕ownerを衣装ownerへ移す。
- 未知画素の昇格はこの処理では行わない。
- 署名済み元画像alpha外への証拠は拒否する。

再生成時の腕owner再割当画素数は、H04 `1,098`、H06 `75,169`、H08 `75,338`。

### B: L04表示

固定paletteでtorsoとmajor_clothingが同色になり、owner修復の意味が表示で見えなくなる問題を修正した。

- 署名済み元画像のRGBだけから、可視owner領域の中央値でpaletteを決める。
- palette policy: `signed-source-visible-owner-median-rgb-v1`
- Stage8 JSON、展開SVG、元画像の三点照合を維持する。

## 検証結果

- H04/H06/H08のPhase5構造: 全例PASS
- L04候補三点監査: `numerical_handoff_eligible=true`, failures空
- B L04 delivery監査: 全例PASS（ブラウザrender含む）
- source silhouette exact: 全例true
- L04 formal: HOLD
- Golden: HOLD
- production: NO_GO

## 独立評価キット

private stagingで差分確認キットv7を生成済み。GitHubへ元画像、NPZ、マスク、座標、比較画像は保存しない。

- キット: `minimalizer-l04-independent-visual-delta-review-kit-20261113-v7`
- 差分票: `L04差分独立視覚確認票.txt`
- 形式: v5の不合格3項目 + H08無回帰1項目
- 差分票が返るまで、L04 formal/Golden/productionは昇格しない。
- private Drive保存: [差分確認キットv7](https://drive.google.com/file/d/1MURpGIbwFDZKgxjjAtj88vTp-YDbt-BJ/view?usp=drivesdk)
- archive: `910009` bytes / SHA-256 `586f3c11c4aee2995b0fd207480b5aa1300cd774559beb1fce6425a7cc0570b1`
- Drive raw readback: sizeとSHA-256がローカル生成物と一致。
- H08 owner認可と現候補の結び付きを確認し、`43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52` を差分キットv8へ同梱した。source SHAは `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e`、候補SHAは `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091`。
- private Drive保存: [差分確認キットv8](https://drive.google.com/file/d/1_uoW2KD6bNFtwwvB1CmuEWV704gPmIUX/view?usp=drivesdk)
- v8 archive: `912044` bytes / SHA-256 `3bad47f9ec90757aa4f05bae058181fab4f1f9d4063def2d1e64a7153353f2ca`
- v8 Drive raw readback: sizeとSHA-256がローカル生成物と一致。
- 再生成時にPhase4 `stage.json`と`metrics.json`のintegration policy不一致を発見し、同じv3 policyを両方へ記録する修正を適用した。見た目の修正ではなく、来歴の整合性修正である。
- 修正後の現行候補receipt SHA-256: `e5b0776638bc3e379be924b1594c9f1286be90a263c7aea7f71b18ee5107001b`
- 修正後の三点監査とB delivery監査: H04/H06/H08全例でfailures空、`B_L04_delivery=PASS`。
- v9は監査JSONの出力先を修正する前の保存物として破棄扱いにし、評価対象にしない。
- 差分確認キットv10: [Drive](https://drive.google.com/file/d/16K_q0dYh3u4WB0huSEWRbNFmQozNtoFn/view?usp=drivesdk), `911508` bytes / SHA-256 `7f251f64d031539b3fd08f87bc916275f91a78f1e6a58817570a57828b957624`。三点監査JSON、B delivery監査JSON、H08 owner認可、現候補metricsをすべて同梱し、Drive raw readback済み。v10を唯一の評価対象とし、v7/v8/v9は再回答に使わない。
- v10の展開済み現行候補フォルダ: [Drive folder](https://drive.google.com/drive/folders/1ZM822kj4107n8rL3EhpnjUxqAmMi7JRI)。zipを展開できない評価者向けに同じv10内容を階層付きで保存した。v5/v4/v3フォルダとは別物で、評価対象はこのv10フォルダだけである。
- 2026-11-13に返却された`L04独立視覚Golden確認票`はv5フォルダ内の候補に対する回答だった。H04 Q3、H06 Q1/Q6が不合格、H08は全問受入だったが、対象receipt SHAの記載がv5と一致し、現行v10 receipt SHA `e5b077...7001b` とは一致しない。これはv10の正式回答としてmaterializeしない。

## 返却後の自動materialize

独立評価者の既存回答は、回答票に記載された対象receipt SHAへだけ結び付く。今回受領した回答がv5候補receipt向けである場合、その回答をv10現候補の回答として読み替えない。v10向けの新しい回答票が返った場合だけ、次のコマンドで差分回答を現行receiptへ固定する。

```cmd
cd /d C:\Work\Projects\_worktrees\minimalizer-codex-h06
python tools\research\materialize_local_l04_visual_delta_receipt.py ^
  "<返却された差分回答.txt>" ^
  "C:\Work\Temp\minimalizer-l04-independent-visual-delta-review-kit-20261113-v10" ^
  --output "<保存先>\L04_INDEPENDENT_VISUAL_DELTA_RECEIPT.json"
```

この処理は、回答票の対象SHA、現行三点監査、B delivery監査、固定済みH08 owner認可receiptを機械的に照合する。不一致や未回答は`HOLD`で停止し、合格しても`L04_formal=PASS`と`Golden=PASS`までで、`production=NO_GO`および`release_authorized=false`を維持する。したがって、v5回答は履歴として保存し、v10の正式receiptへは自動流用しない。

## テスト

- 変更対象およびL04確認系: `20 passed`
- 全体pytestは既存`tests/zerobase`で`playwright`未導入によるcollection errorが発生。これは今回の差分の品質PASSとは別の環境ゲートとして記録する。

## 次の具体的工程

1. v5向けに返却済みの回答は履歴として固定し、v10向け回答とは区別する。
2. v10向け回答が返った場合だけ、`verify_local_l04_visual_delta_review.py`と`materialize_local_l04_visual_delta_receipt.py`で読み戻す。
3. 差分PASSなら、H06/H08 owner receiptと候補receiptを束ねてPhase4 formal reviewを更新する。
4. H04またはH06が不合格なら、該当する具体的欠陥だけを修正し、同じ4問を無条件に繰り返さない。

本記録は候補の機械監査とレビュー経路を記録するもので、独立視覚受入や本番承認の代替ではない。
