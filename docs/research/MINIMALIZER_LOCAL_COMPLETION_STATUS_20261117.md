# MinimalizerLocal 完成状態の現行記録

更新日: 2026-11-17

## この記録の目的

統合開発キャンペーンの現在値を、過去の候補・実験結果と混同しないための
source-freeな現行記録である。これはAの画像品質やPhase4を合格扱いする
receiptではなく、下流工程へ進める条件を固定する台帳である。

## 現行の基準

| 項目 | 現在値 |
|---|---|
| GitHub main | `22d36e88c0b9932cd44e209c8d8be4581098dc62` |
| A branch | `codex/l02-h06-minimal-owner-repair-20261107` / `0edc360f` (`fix_l02_require_unknown_masks`) |
| 採用候補receipt | `381b0b5a...`（v5は対象外） |
| 本番Worker基準 | `64cfeb76e5f8ff4e93b6810880c68f1996348ede` |
| B統合 | PR #462 squash merge済み |
| B merge SHA | `22d36e88c0b9932cd44e209c8d8be4581098dc62` |

## Bの現行結果

PR #462は、Aの画像品質を代行判定せず、L04/L05/L07の安全な経路だけを
mainへ統合した。

- L04三点セットのSHA・相互リンク・HOLD/NO_GO fail-closed検証
- 正式PASS済み入力だけに限定したSVG通常入口
- bundle未設定・候補未登録・HOLD/NO_GOでのPNGフォールバック禁止
- LocalWorkerのbusy状態と900秒超のstale-lock復旧
- sharp-lite、shape-v14、geometry-facetのGitHub CIが全てPASS
- Bのローカル対象テストはPASS（既存warning 1件）

これは本番Workerの置換でも、L04候補の正式昇格でもない。本番反映はAの
意味品質と、同一候補の正式bundle読戻しが揃った後に別途行う。

## Aの現行結果

observer evidence contractは、次を満たさない出力を停止する。

- outerwear / underlayer / sleeve / arm
- `outerwear-underlayer`、`sleeve-arm`、`garment-body`のpairwise遮蔽
- 人物内instance grouping
- source alpha内、配列SHA一致、unknownを陰性化しないこと
- 人手ラベル・既存ownerを推論入力へ持ち込まないこと
- roleごとに正のmaskと独立したunknown maskを持ち、unknownを陰性として暗黙補完しないこと

See-through、Sapiens2、Fashionpedia、FASHN、Grounding-DINO/SAM2の既存資材は、
この六能力を一つの実行可能bundleとして満たさない。See-throughのbody-part
parserを外衣・下層・腕・instanceへ改名することや、depth・連結成分を遮蔽関係
へ読み替えることは不採用とする。

したがって、現在のAは以下のままである。

```text
六能力observer       HOLD
L02                   HOLD
Phase4                FAIL
Phase5                NO_GO
L04 formal / Golden   HOLD
production            NO_GO
```

## 次の実装単位

候補の数画素修正・閾値合わせ・同じレビューの再提出は行わない。次に必要なのは
別人物データで学習可能な六能力入力を成立させることである。

### ルートI: 実行可能checkpoint

固定revision・重みSHA・出力schemaを持つobserverを取得し、H04/H06/H08を同一設定で
source-only推論する。六能力bundleとunknown、pairwise遮蔽、instance IDが揃わなければ
即時HOLDにする。

### ルートII: 別人物データ学習

Live2D/MHP等の別人物データについて、次を非公開側で準備する。

- person instance
- outerwear / underlayer / sleeve / arm
- 3つのpairwise遮蔽
- unknown / not-visible / not-applicable
- source署名、annotation SHA、人物単位のtrain/validation分離

H04/H06/H08はholdout専用とし、学習・閾値決定・早期停止に使用しない。catalogと
training manifestがPASSした後にだけ学習し、固定checkpointで三例を一括推論する。

現在ローカルにはLive2Dモデル資材と抽出コードはあるが、Cubism Core SDK、C++ toolchain、
抽出済みdrawable・pixel annotationが不足している。MHP v2もarm・粗い衣装・instanceの
補助には使えるが、袖とpixel-level pairwise遮蔽が不足するため、そのまま最終observerには
できない。

## 完成判定

次の順序を崩さない。

```text
六能力observerまたは学習入力
  -> H04/H06/H08 source-only一括推論
  -> 構造・意味・視覚の独立Phase4 PASS
  -> H08 owner認可receipt
  -> Phase5 exact replay
  -> L04三点セット読戻し
  -> Golden / 回帰 / PC / iPhone
  -> 本番反映とrollback readback
  -> Drive保存・読戻し・source-free台帳
```

上流のどれかが未達なら、採用候補はDraft/NO_GOのままとする。

