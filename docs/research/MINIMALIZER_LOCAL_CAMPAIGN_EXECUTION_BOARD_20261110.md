# MinimalizerLocal 統合キャンペーン実行ボード

更新日: 2026-11-13
対象: Lane A（実画像品質）と Lane B（L04/L05/L07 統合）  
正本: `origin/main` と、Lane A の Draft PR #449 は分離して扱う。

## まず結論

- **B は実装・統合QAとして完了記録を維持する。** `main` の L04/L05/L07 を作り直さない。
- **Aの現行候補ゲートは成立。** candidate-specific Phase4、candidate-bound Phase5 exact replay、H08 owner-authority receipt、v12独立視覚差分レビュー、L04 formal、Goldenは成立した。六能力observerを含むL02全体はHOLD、現行A候補のproduction/releaseはNO_GO。
- candidate-bound Phase4 bundleはA開発側で生成済み。入力監査はREADY、Phase5構造はH04/H06/H08すべてPASS。H04はマスク変更なしで衣装経由の`neck-attached-to-torso`支持を記録した。
- Aの不足は数画素の追加修正では解消しない。次に必要なのは、同じ未見holdoutへ一括適用できるobserverまたは学習・導入計画の実体である。
- 現行candidate-bound Phase5 bundleの作成者はA開発側、独立評価者は凍結後の後評価者とする。作成手順と保存境界は`docs/research/LOCAL_L02_PHASE5_BUNDLE_CREATION_CONTRACT_20261113.md`に固定した。
- `1887`など旧cap候補は現行方針では採用しない。削除はせず、正本・入力・候補から外した「歴史診断」としてのみ扱う。

### 2026-11-13 v11独立視覚レビュー受領後の判定（履歴）

- `mirano` の確認票をreadbackし、候補との結び付きを検証した。独立性・来歴照合・確認日時は成立。
- H04は設問3 FAIL、H06は設問1/6 FAIL、H08は全設問PASS。
- 全体欄の受入回答は詳細回答と矛盾するため、fail-closedで `review_gate=HOLD` とする。
- 現行候補は正式L04三点セット、Golden、productionへ昇格しない。Bの実装QA完了記録は変更しない。
- 次のA作業はH04/H06の腕・外衣・下層owner再構成を三例共通設計で見直すこと。数画素修正、cap再調整、同じ候補の小刻みな再提出はしない。

### 2026-11-13 現行v12/v8候補の正本判定

- 現行三点セットreceipt SHAは `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a`。v5の `d7faf590…ed2536` は履歴専用で、現行判定へ流用しない。
- v12独立回答はH04/H06/H06 browser/H08、来歴照合、独立性、全体受入がすべてPASS。`L04_formal=PASS / Golden=PASS / release_authorized=false`。
- 完全版キット、formal receipt、B L05/L07 PC/iPhone receiptは同一Driveフォルダへ保存し、サイズreadback済み。
- BはL04 delivery、L05 private HTTPS、L07 Service Worker、PC/iPhone/offline/fallback受入を完了記録として維持する。BはAの品質を判定しない。
- 残る工程は、現行A候補をproductionへ採用するowner最終判断と、採用した場合の本番反映readback。現行A receiptの`production=NO_GO`はこの判断まで維持する。

### 2026-11-13 候補結合器の修正後

- 旧候補のFAILを受け、`candidate_owner` 全身mapを衣装追加maskとして扱っていた結合器を修正した。
- 既知ownerを保持し、未知領域に限定して候補を追加する。これはH04/H06のowner破壊を防ぐ構造修正であり、数画素調整ではない。
- 修正後のH04/H06/H08 Phase5 structural graphはPASS、L04 numerical/alpha gateも再生成済み。ただし視覚Goldenは未実施。
- 新しいv4確認キットを非公開Driveへ保存済み。次の必須工程は、独立評価者がv4の元画像とSVGを再確認し、確認票を返すこと。
- v4確認票を受領するまで、旧v3のFAIL receiptを上書きせず、正式昇格・Golden・本番・mergeを行わない。

### 2026-11-13 確認キット完全性の是正

- 届いたv4回答はH04設問3、H06設問1/6 FAIL、H08 PASSだったが、展開物に `sources/` と監査JSONがなく、候補との正式bindingが成立しなかった。
- 回答は診断記録に留め、旧receiptを上書きしない。確認キット生成器に元画像・SVGの存在チェックを追加した。
- 署名済み元画像、三点セット、candidate audit、B delivery audit、Chrome実描画を一つにまとめたv5を非公開Driveへ保存済み。
- 次の必須工程は、独立評価者がv5を開き、v5内の元画像とSVGを比較して新しい確認票を返すこと。返却まで正式昇格は不可。

### 2026-11-13 v5回答の再照合

- v5として返された確認票は、v4返却票と回答本文SHA-256および確認日時が同一だった。
- H04設問3、H06設問1/6 FAIL、H08 PASSという内容は履歴へ記録するが、v5フォームには候補receipt SHAのbinding欄がなく、現行候補への新規レビュー証拠としては受理しない。
- 確認票生成器・readback検証器を更新し、候補三点セットreceipt SHAをフォームへ埋め込み、キット内receiptと一致しない票をfail-closedで拒否する。
- v6完全キットを非公開Driveへ保存した。次はv6フォームでの新規視覚レビュー返却である。
- v5票は旧候補の診断履歴として保持し、正式receipt・Golden・production・mergeへ昇格しない。

## レーンの役割

| レーン | 判定するもの | 現在地 | Aへの依存 |
|---|---|---|---|
| A | 元画像からの意味的owner、腕・下着・袖・遮蔽、正衣装保持 | **HOLD** | なし。ここが品質の正本 |
| B/L04 | Aが確定した出力を三点セットで安全に表示・展開できるか | **実装QA・現行候補delivery監査完了** | Aの品質を代行せず、現行A候補のrelease認可は別ゲート |
| B/L05 | 実際の入力→出力、PNG/SVG、失敗時応答、fallback | **実装QA・production/device readback完了** | 現行A候補を本番採用するowner判断は別工程 |
| B/L07 | generation-pinned SW、private HTTPS、PC/iPhone、offline復帰 | **実装QA・B production/device readback完了** | 現行A候補のrelease認可とは独立。owner最終採用判断のみ残る |

Bの完了は「品質が合格した」という意味ではない。Bは表示・配信・復旧の契約を検証し、Aの画像品質を代行判定しない。

## 残すデータの分類

### 正本として必ず残す

1. 署名済みH04/H06/H08元画像のsource SHA対応表と、取得日時・署名・保管先。
2. Aのobserver実行設定、モデル／重みのSHA、入力前処理、出力schema、unknownの扱い。
3. 推論後に作成した候補のsource SHA、候補SHA、設定SHA、実行ログ、独立評価receipt。
4. Phase4の独立blind評価と、H06/H08のowner認可receipt。人手ラベルは推論入力ではなく、推論後評価の証拠として残す。
5. Phase5 exact replay、L04元画像・Stage8 JSON・展開SVGの三点照合、L05/L07の実入力・実出力・障害系receipt。
6. 各段階のcommit SHA、PR、テスト結果、判定（PASS/HOLD/FAIL/NO_GO）と、その理由。

### 研究履歴として残すが、正本・採用候補から隔離

- Sapiens2、FASHN、Sapiens、Fashionpedia、Grounding-DINO/SAM2など、六能力を満たさなかったprobe。
- `MICRO_DELTA_ONLY`、`CAPABILITY_HOLD`、`OBSERVER_SEMANTIC_FAIL`となった候補と、そのsource-free集計。
- 旧H04専用、既知例への閾値合わせ、単純OR/AND、class11一律保護、数画素だけの修正履歴。
- 旧L04 cap値（`1887`、`1412`を含む）と、それに基づくDraft候補。現行方針の上限ではない。
- 旧ブランチ、旧PR、旧レビュー。削除や改変はせず、現行正本から参照しない。

### 現行完成判定に残さなくてよいもの

- 仮想環境だけのディレクトリ（例: `C:\Work\SharedAI\minimalizer-observers`）をobserver成果物と誤認するための記録。
- Minimalizerと無関係なReference3DStudio成果物。
- 同一内容を別名で複製した比較画像、再取得できる一時ログ、採用しない候補の私有原画像コピー。

ただし、削除ではなく「非採用・非正本」として扱う。原画像、NPZ、マスク、座標、比較画像はGitHubへ保存せず、必要なものだけ非公開Driveの私有保管へ置く。

## 完成までの一本道

```text
現在
  │
  ├─ B: 完了記録を凍結 ───────────────────────────────┐
  │                                                    │
  └─ A: 六能力observerの導入計画または実体を確定       │
       │                                                │
       ├─ source-onlyでH04/H06/H08を同一設定で一括推論  │
       ├─ unknownを陰性にせず、exclusive ownerを検査   │
       ├─ H04/H06/H08 candidate-specific Phase4 PASS    │
       ├─ H08 owner認可receipt                          │
       ├─ H06/H08/H04 Phase5 exact replay               │
       ├─ H04誤検出修復 + 独立Phase4/5                  │
       └─ A final SHAを固定                             │
                                                        │
                                                        ▼
       B接続: L04三点照合PASS → L05実入出力PASS → L07本番後iPhone PASS
                                                        │
                                                        ▼
       v12 Golden PASS → owner最終採用判断 → A候補本番反映readback → Preserve
```

## 次に行う具体的作業

### 1. Aの入口を一つに固定する

`LOCAL_L02_OBSERVER_ADOPTION_PLAN_20261110.md` と
`local_l02_observer_training_manifest.py` を入口とし、H04/H06/H08を学習・閾値決定に使わないmanifestを受け取る。画像やマスクをGitHubへ置かず、manifestにはSHAと役割だけを書く。

### 2. 六能力を満たさない候補を増やさない

外衣、下着、袖、腕、pairwise遮蔽、instance groupingを同時に監査できないモデルは、候補生成へ進めない。現在の手元資産には該当checkpointがないため、ここは新しい正本入力が必要な状態である。

### 3. observerが揃った後だけ実画像を一括処理する

三例を同一revision・同一設定で処理し、RGB/alpha/source SHA、unknown、4/8連結、穴、遮蔽、exclusive owner、正衣装保持を記録する。H06の見た目が小差分かどうかではなく、意味的に正しいowner修復かを先に判定する。

### 4. Phase4 PASS後にだけ下流へ渡す

現行候補は三例のcandidate-specific Phase4独立PASSとH08 owner認可receiptまで成立し、candidate-bound
全身Phase4 part-mask bundleも生成した。入力監査とPhase5 exact replayはH04/H06/H08すべてPASSした。
H04はマスク変更ではなく、衣装が胴体前面を遮蔽する場合の首→衣装→胴体支持をグラフへ記録して解消した。
旧L04/H06/H08 Stage8成果は流用しない。現行candidateからL04三点セット候補を生成し、Chrome alpha replayと三点SHA照合まで完了した。candidate-triple専用監査もH04/H06/H08でfailures空、数値handoff eligibleとなった。さらにB L04 delivery auditで三例のcross-linkとChrome実描画をPASSした。v12独立視覚回答により`L04_formal=PASS / Golden=PASS`となり、BのL05実入出力・L07本番後iPhone受入も別receiptでPASSした。現行A候補のproductionだけは`NO_GO`を維持する。
FAIL/HOLDの候補はDraft/NO_GOのまま固定する。

## 現在の停止理由

コードのテスト不足ではない。Aの研究テスト、candidate-bound exact replay、L04三点セットの数値・alpha・SHA、v12独立Golden、BのPC/iPhone実機readbackは確認済みである。現在の残りは、六能力observerを含むL02全体の正式完了と、現行A候補をproductionへ採用するowner最終判断・反映後readbackである。Bの既存productionを再変更したり、v5回答を現行候補へ流用したりしない。

この入力が届くまで、旧候補の微修正やcap再調整は行わず、Bの完了記録とA/Bの正本境界を保護する。
