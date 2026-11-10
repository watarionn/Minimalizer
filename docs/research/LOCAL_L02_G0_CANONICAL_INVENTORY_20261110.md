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

private Driveの `Minimalizer_L02_IndependentObservers_20261110` を読み戻し、
H04/H06/H08のFASHN class map・observer receipt・独立observer receipt、H04/H08の
SCHP ATR18/LIP20 class map、H06の既存ATR/LIP NPZとsource-free receiptを含む16件を
確認した。Drive上のファイル名とサイズはローカル保存物と一致した。これらは全て研究観測
であり、owner authorityやPhase4 PASSを付与しない。正式候補を作る時点では、source・
observer・receiptの格納先とreadbackを一つのfreezeへ固定する。

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

## 選択した全身再構成設計

observerをさらに増やすのではなく、Fashionpediaの固定ontologyを持つsource-only
instance segmentationを主衣装observerとして使い、既存ownerを入力にしない
**全身outerwear owner再構成層**を実装した。

```text
signed source
        ↓
Fashionpedia jacket/coat/cardigan/vest/cape instances
        ↓
遮蔽で分断された同一instanceを一つのownerへ束ねる
        ↓
exclusive outerwear owner / unknown / sleeve diagnostic
        ↓
H04,H06,H08一括freeze → 構造・意味・通常倍率レビュー
```

固定契約は次のとおりである。

- model repo `resoa/garment-detector-seg`
- revision `38c0c6bbb27537a76cbbc94a710d8b82fd721b50`
- weights SHA-256 `aafefc440ea8f3f388e894a898e4270a2eeb6e38a3c3ffd3751d07d0f30b26bb`
- 全case共通 confidence `0.30`
- main outerwear class IDs `3,4,5,9,12`
- sleeve classはownerへ昇格せず、独立診断として保持
- 既存owner、human mask、review JSONは推論入力にしない

実装は `tools/research/local_l02_fashionpedia_outerwear_reconstruction.py`、
source-free構造テストは
`tests/test_local_l02_fashionpedia_outerwear_reconstruction.py` に固定した。

### 三例一括probeの結果

以下は推論完了後にのみprivate reviewed maskで照合した診断値であり、閾値選択や推論
入力には使っていない。正式Phase4の値ではない。

| case | owner px | owner components | known TP | known FP | known FN | known-only IoU | status |
|---|---:|---:|---:|---:|---:|---:|---|
| H04 | 55,217 | 1 | 51,272 | 3,459 | 1,300 | 0.915065 | review pending |
| H06 | 316,265 | 1 | 293,101 | 15,394 | 21,722 | 0.887601 | underlayer boundary unresolved |
| H08 | 153,164 | 1 | 149,785 | 183 | 6,785 | 0.955548 | sleeve visual review pending |

H06のknown FPが残っているため、このprobeをPhase4へ昇格しない。通常倍率previewは
非公開Driveの `Minimalizer_L02_FashionpediaOuterwear_20261110` に、NPZ・receiptと同じ
freezeで保存した。独立評価者がH06のカフス／下着、H08の袖、H04の正衣装保持を
意味評価し、候補SHAへ署名を結び付けるまで `Phase4=FAIL` を維持する。

## 追加の設計判定：腕observerの単純合成も採用しない

新たに保存したATR18・LIP20・FASHNのsource-only出力を使い、推論後の診断として腕・手の
union vetoを比較した。H06ではIoUが `0.887601` から `0.911191` へ改善する一方、H08は
`0.955548` から `0.908489` へ低下し、正しい袖の回復を失った。袖診断maskで保護する
変種も、H06 `0.887741`、H08 `0.950465` に留まり、同じ意味owner契約を三例で満たさない。
H04も `0.915173` に留まり、単純な腕vetoを正式候補へ昇格する根拠にはならない。

この結果から、次の候補はobserverのOR/ANDや腕除去ではなく、衣装・腕・下着・遮蔽の
接触componentを一括で意味分割するowner再構成層を必要とする。今回の値は設計棄却の
diagnosticであり、候補へ画素修正を加える根拠にはしない。

## 追加の設計判定：人体パーサー単独の腕vetoは採用しない

Fashionpedia outerwear候補の腕・手境界を補う目的で、別系統のFASHN Human Parserを
同じ署名済み元画像へsource-onlyで実行した。これは候補ownerや評価maskを入力していない。
しかし出力はH06で `top=396,416px`、`arms=0px`、`hands=3,763px`、H08で
`top=209,149px`、`arms=3px`、`hands=3,925px` だった。`top` がコート・下着を
まとめて覆い、腕の観測も不足するため、これを単純な腕vetoやowner-authorityへ
昇格すると、現在の誤owner問題を解決せず別の一括誤除去を作る。

モデル重みSHA-256は
`e43c8c8a9b04f28798f0a4630cf18caa2cdb27a0d454fae43a5716e6f7078244`、設定SHA-256は
`87bd5b66419dbfa7c02cfbeb94e292454863b1606c5df29526b19a6c1de70d9f`。この観測は
**採用候補ではなく設計棄却のsource-only診断**として固定する。次の実装は、人体パーサーの
単純veto追加ではなく、衣装instanceと人体・遮蔽の意味を同時に扱える別の全身owner
設計でなければならない。既存候補を画素単位で再編集しない。

## G0判定

```text
G0 source identity       PASS
G0 source-only boundary  PASS
G0 historical isolation  PASS
G0 semantic owner        CANDIDATE GENERATED / review pending
G0 candidate-bound Phase4 receipt  FAIL / 未結束
L02                      HOLD
Phase4                   FAIL
Phase5                   NO_GO
```

G0で確定したのは正本・失敗クラス・全身候補生成層までである。候補はまだ正式品質成果
ではない。次は同じfreezeに対する独立意味レビューと、H06の誤owner境界の判定へ進む。
