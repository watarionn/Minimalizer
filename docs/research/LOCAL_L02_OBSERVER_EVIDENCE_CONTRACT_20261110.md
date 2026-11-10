# Local L02 observer evidence contract

更新日: 2026-11-10

## 目的

候補生成前に、observerが実際に必要な意味境界を出力しているかを配列レベルで
検査する。`topwear`、`handwear`、または広い`garment`を、外衣・袖・腕・下着・
遮蔽・人物内instanceのowner権限として扱わない。

この契約はownerを生成せず、Phase4を合格にしない。未観測領域はunknownのまま
保持し、人手mask、レビューJSON、凍結ownerは推論入力に認めない。

## 必須のsource-only証拠

一つの正式probeに次の6能力が必要である。

- `outerwear`: 外衣領域
- `underlayer`: 下着・内側衣装領域
- `sleeve`: 袖・衣装側の腕周辺領域
- `arm`: 腕・手など身体側領域
- `occlusion_relation`: 前後関係。`-1=behind`, `0=unknown`, `1=in_front`
- `instance_grouping`: 人物内の衣装instance ID。`0`は未観測

各maskまたは配列は、source alphaと同じ形状で、SHA-256、observer IDを持つ。
source alpha外の正値、SHA不一致、型・形状不一致は即時HOLDとする。

## 実装

`tools/research/local_l02_observer_evidence_contract.py` を追加した。

- `assess_observer_evidence` は6能力の実配列を検査する
- 完全な証拠でも返すのは `CAPABILITY_PASS_RESEARCH_ONLY`
- owner promotion、Phase4、Phase5、Golden、productionの権限は付与しない
- 必須能力の欠落は `CAPABILITY_HOLD`
- source alpha外の観測は fail-closed

既存の `local_l02_observer_capability_gate.py` はobserverの宣言契約を検査し、今回の
配列契約はその後段で実データを検査する。二つを通過して初めて候補生成用のobserver
probeへ進める。

## 現行observerの判定

2026-11-10のSee-through body-part出力は、`topwear`、`handwear`等の広いbody-part
出力を持つが、外衣／下着／袖／腕／遮蔽relation／instance groupingを同時に保証する
出力契約ではない。さらに、保管された候補入力にはsource alpha外の観測画素がある
ため、今回の配列契約では候補入力としても受理しない。

従って現状は次のまま維持する。

```text
observer capability: HOLD
L02: HOLD
Phase4: FAIL
Phase5: NO_GO
Golden: HOLD
production: NO_GO
```

これはH06/H08の数画素修正へ戻る理由にはならない。次に必要なのは、6能力を同一の
source-only実行で満たし、source alpha内に正規化された出力を作るobserverまたは
その導入・学習計画である。

## 検証

```text
tests/test_local_l02_observer_evidence_contract.py: 4 passed
既存A observer/Phase4 focused suite: 38 passed
```

原画像、NPZ、mask、座標、比較画像はこのリポジトリへ保存しない。
