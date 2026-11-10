# Local L02 six-capability observer introduction plan

更新日: 2026-11-10

## 位置づけ

現行のSee-through、Sapiens2、FASHN、SCHPは、単独または単純なOR/ANDでは
`outerwear / underlayer / sleeve / arm / occlusion_relation / instance_grouping`
を同時にowner根拠として出力できない。したがって、observerを追加するたびに
既存ownerへ画素を足す方式は廃止し、以下の導入計画を一つの開発単位とする。

この計画の確定は、observer capabilityの「導入計画」ゲートを満たす。しかし、
実行可能なobserverと凍結出力が揃うまで、Phase4/Phase5/Golden/productionは
昇格させない。

## 目標出力契約

署名済み元画像だけを入力にして、次の配列を同じ実行から出力する。

| 出力 | 内容 | owner権限 |
|---|---|---|
| `outerwear` | 外衣のinstance付き候補 | 単独では不可。下記の整合検査が必要 |
| `underlayer` | 下着・内側衣装候補 | 単独では不可 |
| `sleeve` | 袖・衣装側の腕周辺候補 | 腕との排他検査が必要 |
| `arm` | 腕・手・肌候補 | 衣装削除の直接根拠にはしない |
| `occlusion_relation` | 前後・遮蔽関係。未知を含む | owner割当の補助のみ |
| `instance_grouping` | 人物内の衣装instance ID | instance間の混同防止 |

全出力はsource alpha内、source SHA・model revision・重みSHA・配列SHA付きで、
unknownを陰性へ変換しない。`local_l02_observer_evidence_contract.py`を通過
しない出力は候補生成へ渡さない。

## 導入方式

### 第1段階: observer adapter

既存のSee-throughとSapiens2を読み取り専用の観測層として接続する。

- See-through: topwear、handwear、bottomwear、depth候補
- Sapiens2: arm、hand、garmentの補助候補
- 既存のFASHN/SCHP: 比較用の独立観測。単純OR/ANDでowner化しない
- adapterでroleを付けるが、欠けたunderlayer、occlusion、instanceは推測で埋めない

この段階の成果は、6能力を満たすかどうかの判定receiptだけであり、正式候補ではない。

### 第2段階: 不足能力の導入

第1段階で不足する次のいずれかを、固定revisionの実行可能モデルまたは学習済み
adapterとして導入する。

- outerwearとunderlayerを別instanceで分ける衣装観測
- sleeveとarmの境界観測
- depthまたは明示関係による前後・遮蔽観測
- 人物内instance grouping

既存の広い`topwear`を後処理で外衣へ改名する方法は採用しない。モデル／学習計画の
出力契約が不足している場合は `CAPABILITY_HOLD` とする。

### 第3段階: source-only一括probe

H04/H06/H08を同じコード・同じ設定で実行する。

1. 推論前にレビューJSON、評価mask、既存ownerを開かない
2. source alpha外の観測を拒否
3. roleごとのmask、遮蔽relation、instanceを凍結
4. contact-aware graphで接触・包囲・穴・4/8連結を記録
5. 解けないregionはregion単位でunknownへ退避
6. ownerはこのprobeではまだ正式昇格しない

## observer受入条件

次の全てを満たす場合のみ、候補生成へ進める。

- H04/H06/H08で同じ出力契約が成立
- source-only実行receiptがある
- model repository、revision、全重みSHAが固定されている
- class map、配列、source SHAが一致する
- unknownを陰性化していない
- role間の接触・遮蔽・instance情報が欠けていない
- ライセンス／学習データの利用条件が確認済み
- 推論後の独立レビューに渡すfreeze SHAが作れる

一例だけの成功、候補の画素数、既知例への閾値後合わせ、既存ownerとの差分量は
受入条件にしない。

## 次の実装単位

次に作るのは新しいpixel patchではなく、第1段階のadapterと第2段階の不足能力を
明示するsource-free contract testである。実行可能な6能力observerが用意できない
場合は、候補を生成せず、`CAPABILITY_HOLD`を保ったまま導入待ちとして記録する。

この計画があるため、現在のAは「調査を続ける」状態ではなく、次の実装条件が固定
された状態である。

```text
導入計画確定: PASS
実行observer: HOLD
L02: HOLD
Phase4: FAIL
Phase5: NO_GO
```
