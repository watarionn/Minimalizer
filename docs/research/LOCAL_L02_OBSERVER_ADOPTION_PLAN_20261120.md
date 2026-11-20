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

## 2026-11-20 CandidateBound保管物の照合結果

非公開Driveの `L02_CandidateBound_Phase4_Phase5_20261113` にある `v1` と `v2` を、現行候補の識別子に対して読取照合した。両zipにはH04/H06/H08の `phase_04` と `phase_05`、三例のsource SHA、候補マスクSHA、機械的なmetricsが入っているが、次の現行識別子を正式に束ねるreceiptフィールドはない。

| 保管物 | 読み取れた判定 | 現行版への扱い |
| --- | --- | --- |
| `minimalizer-l02-candidate-bound-phase4-20261113-v1.zip` | `PHASE5_INPUT_PREFLIGHT=PASS/READY`、H04 Phase5 metrics `pass=false` | 過去実験。正式候補へ昇格しない |
| `minimalizer-l02-candidate-bound-phase4-20261113-v2.zip` | `PHASE5_INPUT_PREFLIGHT=PASS/READY`、H04/H06/H08のPhase5 metricsは機械的に `pass=true` | 過去実験。独立Phase4 receiptではない |

両版で記録された候補SHAは、H08 owner認可receipt対象として固定した `43d164…` および本番L04採用receipt `381b0b5a…` と一致しない。したがって、この保管物の `PASS` を現行候補のPhase4 PASS、H08 owner認可、または本番許可へ読み替えない。画像・NPZ・マスクはDrive保管を維持し、GitHubにはこの照合結果とSHA対応だけを残す。

同じ専用Drive直下の署名済みvisual reviewも照合した。評価者の独立性と推論前のラベル非参照は `はい` で、H04/H06/H08の正衣装保持、誤owner除去、遮蔽・重要部位保持も `はい` だった。ただし評価対象は旧候補（H04 `5b568993…`、H06 `87278640…`、H08 `8daafac9…`）である。またH06/H08の「変更結果を視覚的に受け入れられる＝いいえ」は画質劣化ではなく、通常倍率では変更箇所が小さすぎて判定しにくいという意味である。この評価を現行 `43d164…` や `381b0b5a…` の独立Phase4 receiptへ結合しない。

専用Drive直下の現物一覧には、六能力checkpoint、別人物train/validation catalog、またはそれらの学習receiptは見つからなかった。ローカルには追加で `yolo12138/segformer-b2-human-parse-24` のcheckpoint（weights SHA `a14fd5a0…`、config SHA `868488b9…`、processor SHA `1e404d2e…`、revision `9a0e89e…`）が存在し、署名済みH04/H06/H08へ同一設定のsource-only推論を実行できた。しかし正式capability gateで観測できたのは `outerwear`・`sleeve`・`arm` の3能力だけで、`underlayer`、3組の明示的pairwise遮蔽、`instance_grouping` が欠けるため `CAPABILITY_HOLD` となる。これは部分モデルの新規推論確認であって、六能力observer、Phase4入力、現行候補昇格ではない。次に必要なのは新しい閾値調整ではなく、六能力を同一revision・同一設定で出力するcheckpointか、9役割を持つ別人物catalogとtrainer実体の到着である。

なお、ローカル保管のCandidateBound v3/v4/v5/v6/v8も追加照合した。v3/v4/v5/v6/v8はH04 `5b568993…`、H06 `87278640…`、H08 `8daafac9…`を繰り返し記録しており、H08固定対象 `43d164…`ではない。v5はユーザー指定どおり採用対象外とし、版番号だけを根拠に現行候補へ昇格しない。

## 現在の残作業

この計画を満たす実observer checkpoint、署名済み学習メタデータ、train/validationの別人物データ、6能力を揃えたH04/H06/H08の同一設定推論、独立Phase4 PASSは未完了である。従ってこの計画のPASSは、キャンペーン全体の完了を意味しない。

次の実装着手点は、既存候補への微小な後処理を重ねることではない。6能力のうち欠落している下層衣装・袖・ペア別遮蔽・人物内instanceを同一出力契約で生成できるobserver checkpointまたは、別人物データで学習した導入候補を一つに固定し、同じsource-only receipt形式でH04/H06/H08を再推論することである。
