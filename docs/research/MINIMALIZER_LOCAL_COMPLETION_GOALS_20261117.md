# MinimalizerLocal 完成目標・実装手順

更新日: 2026-11-17

## 目的

採用候補receipt `381b0b5a6b52c25472c063c5ca55b65755f3602ab451f569fd6d6a27a20b775a` と、
本番Worker基準 `64cfeb76e5f8ff4e93b6810880c68f1996348ede` を同じ完成版へ結び、
「画像品質」「配信」「実機受入」「復旧」「保存」を別々のPASSで済ませず、最後に一つの
release gateで確認できる状態にする。v5、旧候補、旧Workerの証拠は対象外とする。

## 完成版の定義

完成とは、次の全てが同一候補・同一releaseへ結合され、source-free監査で正式採用可能に
なることをいう。

- A: 六能力observerが実際に使える。出力は外衣、下層衣装、袖、腕、外衣-下層衣装、
  袖-腕、衣装-人物遮蔽の3組、人物内instanceを個別に扱い、unknownを陰性にしない。
- A: 署名済み元画像H04/H06/H08を、ラベル・評価マスク・レビューJSONなしで同一設定推論する。
- A: H06の正衣装保持と腕/下着の誤owner除去、H08の袖回復と排他的owner、H04の誤検出修復を、
  4/8連結、穴、重要部位、遮蔽、unknown保持と併せて確認する。
- A: 凍結後の独立Phase4が、未見・推論前ラベル未使用・評価者独立・意味評価完了・出力凍結・
  review JSON非入力を満たしてPASSする。H08 owner認可receiptも同じ候補へ結合する。
- A: Phase4 PASS候補を、同じsource/config/outputでPhase5 exact replayする。
- B: 元画像・Stage8 JSON・展開SVGの三点SHAが一致し、L04独立レビュー、Golden、production
  bundleが同じ候補へ結合する。
- B: Service Workerのgeneration、rollback、cache境界がsourceと本番runtimeで一致する。
  API・画像・成果物をcacheせず、旧世代を安全に保持する。
- B: 現行WorkerでPCと実機iPhone Safari/PWAを受入し、PNG/SVG保存、機内モード復帰、429
  `Retry-After: 2`、503、再試行、fallback、rollbackを確認する。
- B: L06 Golden、Approved18→78回帰、通常ブラウザ表示、性能を同一候補へ結合する。
- 保存: release SHA、成果物SHA、独立評価、実機受入、復旧結果をsource-free台帳へ記録し、
  private Driveへ保存したreceiptを読戻してSHA一致を確認する。

## 目標一覧

| 目標 | 実装・作業 | PASSの証拠 | 現在 |
|---|---|---|---|
| M0 基準固定 | main/candidate/Worker/A/Bを台帳へ固定 | SHA readback | 完了 |
| M1 observer成立 | checkpointまたは別人物学習をintake。固定revision、重みSHA、unknown分離、六能力契約を確認 | intake receipt | HOLD: 実資材待ち |
| M2 新規推論 | H04/H06/H08をsource-only・同一設定で推論 | source/config/candidate SHA | M1待ち |
| M3 意味品質 | H06/H08/H04を構造単位で評価し、候補を凍結 | 独立Phase4 PASS | M2待ち |
| M4 owner承認 | H08 owner authorityを`43d164…`と候補へ結合 | owner receipt PASS | M3待ち |
| M5 再現 | Phase5 exact replay | exact replay PASS | M3/M4待ち |
| M6 L04昇格 | 三点SHA、独立L04、Golden、production | L04 formal/Golden/production GO | M5待ち |
| M7 L07反映 | source監査、owner反映、runtime監査、rollback確認をruntime binding adapterで結合 | runtime L07 PASS | adapter実装済み・runtime不一致 |
| M8 L05受入 | current WorkerでPC/iPhone Safari/PWA・障害系 | current iPhone binding PASS | HOLD: iPhone未取得 |
| M9 L06結合 | Approved18→78、ブラウザ、性能を現行候補へbinding adapterで結合 | current candidate regression PASS | adapter実装済み・現行証拠待ち |
| M10 release | 9 receiptを一括監査 | `release_authorized=true` | HOLD |
| M11 ship/preserve | owner承認、本番反映、Drive readback、rollback再確認 | final ledger/readback | 未実施 |

## 実行フロー

```text
M0 基準固定
  ↓
M1 observer入力 ──失敗→資材/実行環境を修復（候補を作らない）
  ↓
M2 source-only新規推論
  ↓
M3 独立Phase4 ──FAIL→構造単位でobserver/owner実装を修正し、M2から再実行
  ↓
M4 H08 owner認可
  ↓
M5 Phase5 exact replay
  ↓
M6 L04三点昇格 ─────┐
                     ├→ M10 最終release gate → M11 本番反映・保存・完了
M7 L07 runtime反映 → M8 iPhone受入 ─┤
M9 L06回帰・性能 ─────────────────┘
```

## 具体的な手順

### 1. Aの入力到着時

1. 非公開作業領域へcheckpoint/SDK/catalogを置き、元ファイルのSHAを記録する。
2. `audit_local_l02_observer_intake.py`を実行する。画像、マスク、NPZ、レビューJSONは
   このintake監査へ渡さない。
3. `observer_capabilities`の個別契約、unknown分離、別人物train/validation/holdout境界、
   固定revisionを確認する。
4. 監査PASS後にだけ、署名済みH04/H06/H08元画像を同一設定で一括推論する。
5. source SHA、設定SHA、candidate配列SHA、推論時にラベルを見ていない証拠をmanifestへ固定する。

### 2. Aの候補評価時

1. H06は正衣装を残したまま腕・下層衣装の誤ownerを除去する。
2. H08は袖を回復し、腕と衣装のownerを排他的にする。owner認可は品質PASSの代用にしない。
3. H04は誤検出を修復する。クラス一律保護、単純OR/AND、既知例への閾値後合わせは禁止する。
4. unknownを陰性化せず、4/8連結、穴、重要部位、遮蔽、遮蔽下の意味を評価する。
5. 候補を凍結し、独立評価者がPhase4を実施する。同じ候補へH08 owner receiptを結合する。
6. Phase4 PASS後、同一候補のままPhase5 exact replayを実行する。

### 3. Bの反映・受入時

1. L04で元画像・Stage8 JSON・展開SVGを三点照合する。これはAの意味品質を代替しない。
2. source側SW監査をPASSさせる。runtimeの未追跡`dist/`は削除・上書きしない。
3. owner承認済みの既存反映手順だけでruntimeへ反映し、runtime SHA、SW generation、hash、
   `/health`を読み戻す。旧世代保持とrollbackを確認する。
4. runtime L07 PASS後に、PC、iPhone Safari、PWAの順でPNG/SVG保存、機内モード復帰、429/503、
   retry/fallback/rollbackを受入する。旧WorkerのiPhone receiptは再利用しない。
5. iPhone raw receiptをprivate領域へ置き、current Worker SHAへbindingして監査する。
6. L06回帰と性能を同一候補へ結合する。

### 4. 最終化時

1. A、Phase4、Phase5、L04、L05、L07、L06、実機受入、保存のreceiptを一括監査する。
2. `release_authorized=true`になるまでmerge、正式release、本番完了宣言をしない。
3. owner承認後にだけ本番反映し、反映後の通常入口、health、PNG/SVG、rollbackを再確認する。
4. private Driveを読戻してSHAを確認し、GitHubにはsource-freeコード・テスト・メトリクス・
   台帳だけを残す。

### 5. L06現行候補結合の追加手順

1. Phase14 summaryへ採用候補SHAを明示し、Approved18/78とDiagnostic2の入力SHAを記録する。
2. 同じ候補SHAを持つブラウザ表示・性能receiptを作成する。
3. `bind_local_l06_regression_candidate.py`で両receiptとbinding SHAを監査する。
4. 旧summaryに候補SHAがない場合は `SUMMARY_CANDIDATE_BINDING_MISSING_OR_MISMATCH` のまま止め、
   旧結果を現行候補のL06 PASSへ読み替えない。

### 6. L07 runtime結合

1. owner承認済み手順でruntimeへ反映し、反映前後のWorker SHAを読み戻す。
2. runtimeのSW世代、source世代、旧世代保持、rollback、cache境界をJSON receiptへ記録する。
3. `/health`のHTTP 200、`runtime_error=null`、`zerobase2_authorized=true`を別receiptへ記録する。
4. `bind_local_l07_runtime_release.py`で両receiptのSHAと候補/Worker SHAを結合する。
5. runtime監査が旧SW削除やgeneration mismatchを返した場合は、owner反映を修復してから再実行し、
   手作業でPASSへ変更しない。

## 現在の停止点

- M1: 六能力observerの実行可能checkpoint/SDKまたは別人物学習catalogが未到着。
- M7: 本番runtimeは旧SW `minimalizer-local-20261107-1`で、旧世代cache削除のためL07 HOLD。
- M8: 現行Worker `64cf…`に結び付いたiPhone receiptが未取得。
- M9: 旧Phase14 regression summaryは現行候補SHAを持たないため、L06 adapterで結合HOLD。
- M10/M11: 上記が未完了なので正式release、本番反映、完成宣言は不可。

この文書は作業を小さな画素修正へ分解するためのものではなく、各ゲートを一度の構造的な
実装・評価へまとめるための完成目標である。
