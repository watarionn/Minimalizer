# L02 observer 入力到着時の実行手順

この手順は、六能力observerまたは別人物学習入力が届いたときの最初の
source-free判定を固定する。GitHubにはコード・メタデータ・SHAだけを置き、
元画像、マスク、NPZ、座標、レビュー画像は非公開作業領域から出さない。

## 判定前の禁止事項

- H04/H06/H08の元画像、マスク、NPZ、レビューを推論前に開かない。
- 人手ラベルを推論入力、閾値決定、早期停止へ使わない。
- 既存のH04/H06/H08評価用資材を学習データへ流用しない。
- `occlusion_relation`のような一般名、単純OR/AND、既知例への閾値合わせで
  六能力を名乗らない。

## ルートI: 固定checkpoint

非公開作業領域に次の二つを置く。

- observer仕様JSON
- observer重みファイル

仕様JSONは少なくとも次を含む。

```json
{
  "schema": "minimalizer/l02/observer_checkpoint/v1",
  "observer_id": "<固定ID>",
  "revision": "<固定revision>",
  "weights_sha256": "<重みSHA-256>",
  "source_only": true,
  "human_labels_used_for_inference": false,
  "unknown_policy": "separate_from_negative",
  "same_config_cases": ["H04", "H06", "H08"],
  "output_contract": [
    "outerwear", "underlayer", "sleeve", "arm",
    "occlusion_outerwear_underlayer",
    "occlusion_sleeve_arm",
    "occlusion_garment_body",
    "instance_grouping"
  ]
}
```

cmdで次を実行する。

```text
python tools\research\audit_local_l02_observer_intake.py checkpoint --spec <非公開observer仕様JSON> --weights <非公開重み> --output <非公開checkpoint-intake.json>
```

`CAPABILITY_PASS_RESEARCH_ONLY` のときだけ研究probeへ進める。これはPhase4や
本番の許可ではない。重みSHA、三組遮蔽、unknown分離、三例同一設定のどれかが
不足した場合は `CAPABILITY_HOLD` のまま修正へ戻る。

## ルートII: 別人物学習入力

非公開作業領域に、Cubism Core SDKとsource-free catalog JSONを置く。SDKの必要構成は
次のとおり。

```text
Core\include\Live2DCubismCore.h
Core\lib\windows\x86_64\Live2DCubismCore.lib
Samples\Common\
```

catalogは別人物のtrain/validationとH04/H06/H08 holdoutを人物単位で分離し、
source SHA、source署名receipt SHA、annotation SHA、9役割、3組遮蔽、person instance、
unknown、`labels_in_inference_input=false` を持つ。catalogのsource/annotation実体は
非公開のままにする。

cmdで次を実行する。

```text
python tools\research\audit_local_l02_observer_intake.py training --sdk-root <非公開Cubism SDK> --catalog <非公開catalog.json> --output <非公開training-intake.json>
```

`TRAINING_INPUT_PASS_RESEARCH_ONLY` のときだけ、別人物データで学習runnerを実行する。
学習後は重みSHAと出力契約を固定し、H04/H06/H08を同一設定で一括推論する。

## 固定checkpointの三例一括probe

intake監査が `CAPABILITY_PASS_RESEARCH_ONLY` を返した後、次のsource-only adapterを実行する。
adapterはレビューJSON、評価マスク、既存owner配列を引数に受け取らず、各ケースについて次のNPZキーだけを出力する。

```text
outerwear_mask / outerwear_unknown
underlayer_mask / underlayer_unknown
sleeve_mask / sleeve_unknown
arm_mask / arm_unknown
occlusion_outerwear_underlayer
occlusion_sleeve_arm
occlusion_garment_body
instance_grouping
```

cmdでは署名済み元画像を指定して次を実行する。`<adapter.py>`は固定した推論adapter、
`<spec.json>`と`<weights>`はintake監査に使った同じファイルである。出力先は非公開作業領域に置く。

```text
python tools\research\run_local_l02_observer_probe.py --spec <spec.json> --weights <weights> --adapter <adapter.py> --h04 <H04署名元画像> --h06 <H06署名元画像> --h08 <H08署名元画像> --output-dir <非公開probe出力フォルダ> --receipt <非公開probe receipt.json>
```

成功時は `PROBE_FROZEN_RESEARCH_ONLY` となり、三例のsource SHA、出力NPZ SHA、各配列SHA、
共通推論設定SHAをreceiptへ記録する。出力NPZとreceiptは非公開Driveへ保存し、GitHubにはreceiptの
source-free要約だけを残す。adapter失敗、source SHA不一致、unknownの欠落、遮蔽pairの欠落、
instance groupingの空、またはalpha外出力が一つでもあれば全体をHOLDとし、Phase4へ進めない。

## intake PASS後の順序

1. source-onlyで三例を新規推論し、推論receiptを凍結する。
2. H04誤検出、H06正衣装保持・腕/下着誤owner、H08袖回復・排他的ownerを確認する。
3. 凍結出力を独立評価者へ渡し、Phase4を実施する。
4. Phase4 PASS後だけ、同じsource SHA・設定・observer SHAでPhase5を再現する。
5. L04三点セット、回帰、実機受入、release gateへ候補SHAを結合する。

intake監査のPASSだけで候補を昇格したり、既存評価を新しいobserverの証拠へ
読み替えたりしてはならない。
