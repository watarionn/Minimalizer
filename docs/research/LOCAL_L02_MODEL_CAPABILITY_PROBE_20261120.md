# L02 モデル能力プローブ記録（2026-11-20）

## 目的

署名済みH06/H08元画像へ、推論前に評価マスク・owner配列・人手ラベルを
渡さず、同一設定の公開semantic parserを実行した。これは品質評価ではなく、
六能力observerへ接続できる出力が本当に存在するかを確認するsource-free記録である。

## 実行対象

- model: `yolo12138/segformer-b2-human-parse-24`
- model config SHA-256: `868488b985caa2b4e202a9a42646b27dbab97c83d75722f7d9e41969f6635eb1`
- cases: H06, H08
- same-config inference: yes
- human labels used for inference: no
- owner arrays used for inference: no
- unknown policy: `separate-from-negative`
- runner: `tools/research/run_local_l02_model_capability_probe.py`
- private result: `C:\Work\Temp\minimalizer-l02-model-probe-20261120\human-parse-24_receipt.json`

## 出力能力

| 必要能力 | 現物確認 | 判定 |
|---|---|---|
| 外衣 | `coat_only_torso_region` head | 出力あり。ただし意味品質は未評価 |
| 下層衣装 | 明示headなし | 欠落 |
| 袖 | 左右sleeve head | 出力あり。ただし意味品質は未評価 |
| 腕 | 左右arm head | 出力あり。ただし意味品質は未評価 |
| ペア別遮蔽 | pairwise出力なし | 欠落 |
| 人物内instance | instance-id出力なし | 欠落 |

## ゲート

`CAPABILITY_HOLD_RESEARCH_ONLY`。下層衣装・ペア別遮蔽・人物内instanceを
top/upper-clothes、袖と腕のOR/AND、単一人物前提で補ってはいけないため、
Phase4はHOLD、Phase5はNO_GO、GoldenはHOLD、ProductionはNO_GOを維持する。

## 次の実装条件

明示的な下層衣装head、pairwise occlusion head、人物内instance出力を持つ
observerまたは、別人物データで学習した同等のマルチヘッドobserverを用意し、
その後にのみ三例同一設定のsource-only probeと凍結後独立Phase4評価へ進む。
この記録のNPZ・原画像・マスクは非公開領域に置き、リポジトリへ追加しない。
