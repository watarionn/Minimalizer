# MinimalizerLocal 統合キャンペーン実行ボード

更新日: 2026-11-10  
対象: Lane A（実画像品質）と Lane B（L04/L05/L07 統合）  
正本: `origin/main` と、Lane A の Draft PR #449 は分離して扱う。

## まず結論

- **B は実装・統合QAとして完了記録を維持する。** `main` の L04/L05/L07 を作り直さない。
- **A は未完了。** H06/H08/H04の意味的owner修復に必要な六能力observerがまだないため、L02はHOLD、Phase4はFAIL、Phase5・Golden・本番はNO_GO。
- Aの不足は数画素の追加修正では解消しない。次に必要なのは、同じ未見holdoutへ一括適用できるobserverまたは学習・導入計画の実体である。
- `1887`など旧cap候補は現行方針では採用しない。削除はせず、正本・入力・候補から外した「歴史診断」としてのみ扱う。

## レーンの役割

| レーン | 判定するもの | 現在地 | Aへの依存 |
|---|---|---|---|
| A | 元画像からの意味的owner、腕・下着・袖・遮蔽、正衣装保持 | **HOLD** | なし。ここが品質の正本 |
| B/L04 | Aが確定した出力を三点セットで安全に表示・展開できるか | **実装QA完了記録を維持** | Aの最終SHAを受け取るまで正式handoffは不可 |
| B/L05 | 実際の入力→出力、PNG/SVG、失敗時応答、fallback | **実装QA完了記録を維持** | Aの最終候補接続は未実施 |
| B/L07 | generation-pinned SW、private HTTPS、PC/iPhone、offline復帰 | **実装QA完了記録を維持** | 本番反映後のiPhone受入だけ残る |

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
       ├─ H06独立Phase4 PASS                            │
       ├─ H06 Phase5 exact replay                       │
       ├─ H08独立Phase4 PASS + owner認可receipt         │
       ├─ H08 Phase5 exact replay                       │
       ├─ H04誤検出修復 + 独立Phase4/5                  │
       └─ A final SHAを固定                             │
                                                        │
                                                        ▼
       B接続: L04三点照合 → L05実入出力 → L07本番後iPhone
                                                        │
                                                        ▼
       Golden全件 → owner承認 → 本番反映 → 実機受入 → Preserve
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

Phase4が三例で独立PASSするまで、Phase5正式昇格、H08 owner認可receiptの採用、L04正式三点セット、Golden、本番反映を行わない。FAIL/HOLDの候補はDraft/NO_GOのまま固定する。

## 現在の停止理由

コードのテスト不足ではない。Aの研究テストは `479 passed`、Bの統合回帰は `67 passed` だが、これは構造・契約の確認であり、六能力observerの意味品質やPhase4 PASSを証明しない。現在の次の外部入力は、実行可能checkpointまたは、学習・導入計画を実行できるデータ／重み／revisionの組み合わせである。

この入力が届くまで、旧候補の微修正やcap再調整は行わず、Bの完了記録とA/Bの正本境界を保護する。
