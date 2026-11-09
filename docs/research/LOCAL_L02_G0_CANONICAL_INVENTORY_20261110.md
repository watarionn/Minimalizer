# L02 G0基準台帳と意味クラス別失敗表

更新日: 2026-11-10

この台帳は、H04/H06/H08の既存資料を「正式入力」「比較専用」「研究観測」「未結束」
に分類するためのsource-free台帳である。ここで候補を昇格させない。旧資料を削除せず、
正式な推論経路から隔離する。

## 現在の正本

| 対象 | 現在値 | 判定 |
|---|---|---|
| `origin/main` | `54654bfac80550a4fe565de694c39d30b47b5703` | readback済み |
| Lane A PR #449 | Draft、G0開始時のremote head `0123b3895383b86bf8a978c9cd8f6132a021f0fa` | 品質候補なし |
| Lane B PR #451 | head `c593b46c53c28127b08d74d2ce733045495b5577` | Aと独立して保持 |
| A L02 / Phase4 | `HOLD` / `FAIL` | 継続作業 |
| Phase5 / L04 handoff | `NO_GO` / `false` | Phase4 PASSまで禁止 |
| Golden / production | `HOLD` / `NO_GO` | owner操作・反映なし |

## G0で正式入力として保持するもの

### signed source

| case | source | encoded SHA-256 | RGBA SHA-256 | 取扱い |
|---|---|---|---|---|
| H04 | `ReviewedEvidence/H04_original_signed_from_trace.png` | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | `4eaf402c1375cad2f4d5d0f3350458ef7a80e9ceb9ca2b4a157d0d66651545f4` | 正式入力候補 |
| H06 | `DualObserver/raw_signed/H06.webp` | `c32014932927fd6b290e2f9ec5970ef2bbb92650ab2ff758574076f0dc3352b8` | `c4c4891542c80d9d2f61c45c1b6794722e5dfceed837179ae83352995e4522b5` | 正式入力候補 |
| H08 | `DualObserver/raw_signed/H08.webp` | `759b4ed81a49b0e9fce31e6134189a7169ec3c134c3fc97d22d4d0fd6a344a9e` | `5107f0eeb3b950b8e93ceb3fb6f98c52ecf6e2ce94d39c1ee606f3fad1e8026c` | 正式入力候補 |

H08のRGBA SHAは、手元のsource-only observer receiptに記録された値を使用する。encoded
source SHAと照合できないRGBA値は、候補生成の入力にしない。

### source-only observer

現在の観測資料は、Sapiens2、SCHP ATR18、SCHP LIP20、DeepFashion2、FASHN Human
Parserの出力である。いずれも以下の扱いに固定する。

- signed sourceだけを入力にする
- 人手mask、レビューJSON、既存ownerを推論入力にしない
- `unknown`を陰性へ変換しない
- class map、model revision、重みSHA、出力SHAをreceiptへ束縛する
- observer間の一致をowner権限とみなさない
- outerwear owner authorityを持たない観測は研究資料のままにする

FASHN出力は全身再観測の資料として保存するが、receipt自身が
`outerwear_owner_authority=false`、`research_only=true`、`Phase4=FAIL`を示している。
新observerの追加だけで候補を作らない。

## 参照専用へ隔離するもの

次の成果はSHAと来歴を保持するが、正式推論入力・Phase4候補・Phase5入力には戻さない。

| 資料群 | 理由 |
|---|---|
| Run30 H04/H06/H08 owner 4/8配列 | 既存ownerを基準にした旧候補 |
| `CodexExactReplay` / `Guarded` | receiptが `candidate_only`、`Phase4=FAIL` |
| `IndependentObserver` / `IndependentObserverReplay2` | observer合意の診断でありowner authorityではない |
| `NewObserver20261110` | source-only観測だが、衣装owner権限なし・未評価 |
| 旧cap、旧Stage8、旧SVG、label付きpost-score | 現行候補の正式証拠ではない |
| 旧 `FORMAL_GATE_VERIFICATION_STATUS.json` | `NOT_INDEPENDENTLY_VERIFIED_IN_THIS_RUN`を含む歴史台帳 |
| 旧 `OBSERVER_PROVENANCE_LICENSE_AUTHORITY.json` | 旧来の保留記録。ライセンスゲートの正本にはしない |

private Driveの既存observerフォルダは読み戻しできた。現時点の直下にはH04/H08の
independent observer receiptとATR/LIP NPZがあり、H06の同名receiptはこのフォルダの
直下にはない。これはDrive全体に存在しないという意味ではなく、現行フォルダのreadback
事実である。新しい検索を広げず、正式候補を作る時点でsource・observer・receiptの
格納先を一つに固定する。

## 意味クラス別失敗表

### H06

| 失敗クラス | 観測された事実 | 根本課題 | 局所修正を禁止する理由 |
|---|---|---|---|
| 正衣装／腕境界 | ATR upperに腕733px、underlayer1,883px、unknown33,144px | 上衣の外形だけでは腕・下着との意味分離ができない | 4px除去ではknown-negative owner 11,547pxが残る |
| 袖・衣装接触 | 最大の衝突componentが人物本体の大成分 | 接触境界と遮蔽順序が未確定 | 小領域の橋渡しは意味境界を変えない |
| unknown | observer bundle全体でunknown52,428px | 未観測領域を陰性化できない | unknownを埋める閾値後合わせは禁止 |
| 視覚受入 | 旧候補の変更量が小さすぎる | 意味クラス全体の変更になっていない | `MICRO_DELTA_ONLY`として候補外 |

### H08

| 失敗クラス | 観測された事実 | 根本課題 | 局所修正を禁止する理由 |
|---|---|---|---|
| 正衣装／腕境界 | ATR upper腕678px、LIP coat腕5,906px、unknownが大きい | observerごとに腕混入と再現性が異なる | 591px回復では未回復領域59,444pxが残る |
| 袖・遮蔽 | 最大衝突componentが人物本体の大成分 | 袖と腕、外衣と下着の前後関係が未決定 | 小領域回復では遮蔽順序を再構成できない |
| unknown | observer bundle全体でunknown106,004px | 観測不一致をownerへ昇格できない | OR/ANDで埋めると誤ownerを増やす |
| 視覚受入 | 変更結果が小さすぎる | レビュー可能な全身変化になっていない | 正式候補にしない |

### H04

| 失敗クラス | 観測された事実 | 根本課題 | 局所修正を禁止する理由 |
|---|---|---|---|
| 正衣装／腕境界 | ATR upperのknown-negative28,488px、LIP coat74,716px、交差でも23,311px | H06/H08のobserver規則を移植できない | H04固有の閾値・ラベル移植は禁止 |
| observer衝突 | 全役割unionでrole conflict 3、unknown20,727px | 意味境界の観測根拠が不足 | 単純unionは衣装全体を誤owner化する |
| 全身候補 | 旧候補の変更0px | まだ全身owner再構成を実行していない | H06/H08の部分結果を流用しない |

## 三例共通の根本欠落

1. observerのrole evidenceを接触境界・遮蔽順序と結び付けるowner-authority層がない。
2. 大きな人物componentを、腕・袖・下着・正衣装へ同じ規則で分割できていない。
3. `unknown`を保持したまま、意味ownerを排他的に決める全身候補がまだない。
4. 独立評価資料を候補SHAへ束縛した正式Phase4 receiptが、現行候補として完成していない。
5. AのPhase4 FAILをBの表示QAで補うことはできない。

## 次に選ぶ設計

次の実装は、observerをさらに増やすことではなく、既存のsource-only observer bundleを
入力にした**全身owner再構成層**とする。

```text
source-only observer role maps
        ↓
role-specific regions + contact/occlusion graph
        ↓
coherent component単位の意味分割
        ↓
exclusive owner / unknown / occlusion result
        ↓
H04,H06,H08一括freeze → 構造・意味・通常倍率レビュー
```

この層で最大衝突componentを三例同時に分割できない場合、閾値や画素パッチへ戻らず、
「現在の観測だけではowner authorityが不足」と判定する。その場合はモデル／観測経路の
変更を一回の設計変更として行い、局所候補は作らない。

## G0判定

```text
G0 source identity       PASS
G0 source-only boundary  PASS
G0 historical isolation  PASS
G0 semantic owner        FAIL / 未実装
G0 candidate-bound Phase4 receipt  FAIL / 未結束
L02                      HOLD
Phase4                   FAIL
Phase5                   NO_GO
```

G0で確定したのは「どの資料を使うか」と「何が根本欠落か」までである。これを完了扱い
せず、次は全身owner再構成層の設計レビューへ進む。
