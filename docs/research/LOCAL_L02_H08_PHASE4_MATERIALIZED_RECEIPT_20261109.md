# H08 Phase4 materialized receipt（2026-11-09）

Status: **FAIL / L02 HOLD / Phase5 NO_GO / production NO_GO**

これは、所有者が固定した H08 frozen owner map を既存の source-only replay へ再入力して得た、private candidate output の来歴と結果だけを記録する source-free receipt である。新しい推論規則・閾値・手作業ラベル入力は追加していない。

## 入力と実行

| 項目 | SHA-256 |
| --- | --- |
| signed H08 source | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` |
| selected frozen owner | `43d164d934614fce104f5cd3da1519e95571d81c287c107b99cdf53db2766c52` |
| class IDs | `d6ff3cee53338711f6dc253dc423d772f52d7cce711d3311a6497002739976f5` |
| independent observer | `3dd9b6e01d2584247543abbe64f543e1ec1d0d55ab6231d3d7d2783a2d0cbcfa` |
| replay helper code | `fa3bc13b08940c40e0322db30b6e5456db2981054995af0db296be4007211b35` |
| post-freeze review mask | `e73e3e083500ff7524fca3c1d0d91d1ce3845616230c80e9c992e1a726fe8f46` |

人手マスク・review JSON は candidate freeze の後にだけ使用し、unknown を陰性として扱っていない。

## Materialized output

- owner candidate array SHA: `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091`
- private NPY file SHA: `c443d6a35ffa164749c5c92259652df02e59e9a189ae98a766249d4282c9e07e`
- candidate owner promotions: 591px（owner1: 588px、owner2: 3px）
- private materialized receipt SHA: `5aa905fda27b65e3493ba251aa7bc2a3e82b89fadc15b5622ba479bb72903419`
- replay: 2回でcandidate/receipt SHA一致

private Drive readback:

- candidate: `1jr4UJM3FRkRIpe-k2P-3z1pAiOoLiQTa`、4,000,128 bytes
- receipt: `1qr-iXI7xWgmGRYfB4Gb9pvMGqRE7LRm_`、2,651 bytes

## 検証結果

| gate | 結果 |
| --- | --- |
| source alpha 外への出力 | PASS（0） |
| exclusive owner 4/8 components | PASS（`[29,22,14,11]` 不変） |
| enclosed holes | PASS（`[3,1,3,1]` 不変） |
| post-freeze labelled IoU | 0.280547 |
| positive recall | 0.283892 |
| known-negative false owner | 4,049px 残存 |
| correct clothing recovery | FAIL |
| wrong-owner removal | FAIL |
| critical parts / occlusion | この再生だけでは独立materializeしていない |
| Phase4 | FAIL |

## 結論

対象取り違えのない candidate output と private preservation は完了した。しかし、この候補はH08の袖回復も誤owner除去も完了していない。したがって Phase5、Golden、production には進めない。次の実装工程は、この固定receiptをベースラインとして、H08の残存4,049px誤ownerと243,186pxのlabelled garment FNを最初の失敗点として扱う。
