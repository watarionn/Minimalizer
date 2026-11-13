# L02 六能力observer 導入・学習計画

更新日: 2026-11-10

## 位置づけ

これは新しい画像候補やPhase4 receiptではない。現在の手元observerが欠いている六能力を、
外部checkpointの導入またはアニメ向け学習で埋めるための、source-freeな実装契約と受入計画である。
この計画を満たすobserverが固定されるまで、既存候補の画素修正、閾値調整、owner認可、
Phase4、Stage8昇格は行わない。

## 現在の判定

2026-11-10時点のprobeでは、See-through body-part parser、SAM-HQ 19部位、Sapiens2、
Fashionpedia、Grounding-DINO+SAM2のいずれも、六能力を同時に満たさない。
`topwear`の残差を`underlayer`へ改名したり、人物foregroundの連結成分をgarment instanceへ
読み替えたり、二層のdepth差を全遮蔽関係へ拡張したりしてはならない。

判定は次のとおり。

```text
observer capability gate  HOLD
L02                         HOLD
Phase4                      FAIL
Phase5                      NO_GO
Golden / production         HOLD / NO_GO
```

## 必須出力契約

observerはH04/H06/H08を同じrevision、重み、入力前処理、出力契約で処理し、次を一つの
凍結可能なbundleとして出力する。ケース別prompt、閾値、座標、後処理分岐は契約違反とする。

| 能力 | 必須出力 | 最低限の意味 |
|---|---|---|
| `outerwear` | bool mask + garment instance ID | 外衣を下層・腕・袖から分離 |
| `underlayer` | bool mask + garment instance ID | 外衣の内側に見える衣装層。広い`topwear`残差では不可 |
| `sleeve` | bool mask + garment instance ID | 袖・カフを腕・手から分離 |
| `arm` | bool mask + body instance ID | 肌の腕領域。袖に覆われる部分はunknownを許可 |
| `occlusion_relation` | role pairごとの前後関係 + unknown | 少なくとも外衣/下層、袖/腕、衣装/身体の関係を別々に表現 |
| `instance_grouping` | pixel-to-instance ID + instance type | 同一人物内のgarment/body instanceを結び付ける |

各maskはsource alpha内、SHA・shape・dtype付きでなければならない。unknownは陰性に変換せず、
衝突する接触componentはcomponent全体をunknownへ戻す。owner mapはobserver出力ではなく、
このevidence bundleを後段のcomponent solverへ渡した後にだけ生成する。

### 遮蔽関係の表現

現在のscalar `occlusion_relation`（一枚の`-1/0/1`配列）だけでは、複数role pairの関係を
監査できない。導入時の正式schemaは、次のようなpair単位を必須にする。

```text
relations[
  {role_a: outerwear, role_b: underlayer, values: int8[H,W]},
  {role_a: sleeve,    role_b: arm,        values: int8[H,W]},
  {role_a: garment,   role_b: body,       values: int8[H,W]}
]
```

`-1=behind`、`1=in_front`、`0=unknown`とし、重なりのない画素を関係の証拠として扱わない。
pairの欠落は能力不足であり、depth画像一枚の存在だけではPASSにしない。

## 導入ルート

### ルートI: 実行可能checkpointを採用

候補modelを見つけた場合は、名前や論文ではなく、次の順で採用可否を決める。

1. ローカルでrevision、重みSHA、license metadata、推論依存関係を固定する。
2. signed sourceだけを入力にして、H04/H06/H08を同一設定で一括実行する。
3. 出力bundleが上記六能力schemaを満たすか、source-free contract testで検査する。
4. H04/H06/H08すべてで非空の意味境界、unknown、pairwise遮蔽、instance IDが再現することを確認する。
5. その後にだけ、候補を一つ生成し、独立Phase4へ渡す。

単一semantic mask、人物全体instance、`topwear`の改名、depthからの推測だけではルートIを
通過させない。

### ルートII: Minimalizer用observerを学習

ルートIのcheckpointが確定できない場合は、既存候補を教師にせず、次のデータ設計から始める。

- 人物instance、外衣、下層、袖、腕、接触境界、遮蔽pairを別annotationとして持つ。
- unknown / not-visible / not-applicableを陰性と分ける。
- H04/H06/H08は受入専用の未見holdoutにして、学習・閾値決定・早期停止には使わない。
- train/validationには別のアニメ人物・衣装・ポーズ・遮蔽を用意し、人物単位で分離する。
- mask loss、boundary loss、pairwise occlusion loss、instance grouping lossを分けて記録する。
- 出力は推論前にラベルを必要とせず、推論後の独立評価だけが人手annotationを読む。

学習完了の定義はlossや平均IoUではなく、未見holdoutで六能力bundleを生成でき、構造・意味・
通常倍率の視覚ゲートを三例同時に通過することとする。

## 受入ゲート

```text
N0  契約検査       six capabilities / pairwise relation / instance schema
N1  source-only    signed source only, labels/old owners/review absent
N2  三例一括        H04/H06/H08 same code and settings
N3  構造           alpha, dtype, SHA, exclusive owner, 4/8-connectivity, holes, unknown
N4  意味           outerwear, underlayer, sleeve, arm, occlusion, correct garment retention
N5  視覚           normal scale and enlarged boundary review; material change, not micro-delta
N6  freeze         one candidate SHA + observer/output/model receipts
N7  Phase4         independent signed blind review PASS for all three
```

N0-N6のどこか一つでもFAILなら候補は破棄し、同じ候補へ画素修正を重ねない。N7 PASS前の
Phase5、L04 formal handoff、Golden、本番反映はNO_GOのまま維持する。

## 実装順序

1. `local_l02_observer_evidence_contract.py`をpairwise relation schemaへ拡張する。
2. ルートIの候補checkpointを、三例一括の能力probeだけで比較する。
3. ルートIが成立しなければ、annotation schema、学習split、loss、再現コマンドをsource-free
   計画として固定し、私有データはDriveへ分離保存する。訓練manifestは
   `tools/research/local_l02_observer_training_manifest.py`で検証し、H04/H06/H08のholdout
   混入、人物単位のsplit漏洩、unknownの陰性化をfail-closedにする。
4. 六能力bundleがN0-N6を通ったときだけ、一つの全身candidate packageを生成する。
5. 独立Phase4が三例PASSした後、Aのfreeze SHAをBへexact handoffする。

## 保存境界

GitHubにはこの計画、schema、source-free code、tests、metrics、gate結果だけを保存する。
原画像、mask、NPZ、座標、比較画像、学習データは非公開Driveに保存し、SHAとreadbackだけを
GitHub側へ記録する。現行のSAM-HQ、See-through、Sapiens2、Fashionpediaの出力は研究履歴で
あり、正式候補へ戻さない。
