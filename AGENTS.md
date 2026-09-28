# AGENTS.md — Minimalizer / ZeroBase 2nd Cycle 開発ルール（Codex向け）

このリポジトリで作業するCodexは、作業開始前にこのファイルと `docs/zerobase/ZEROBASE_2ND_CYCLE_DESIGN.md` を読むこと。

## 1. 何を作っているか

Minimalizerは、キャラクター画像を「人物構造・主要色塊・識別特徴を保ちながら、少数の大きな幾何形状へ単純化する」ツールである。

現在の再設計系は **ZeroBase 2nd Cycle**。1st Cycleでは foreground coverage を人物理解と誤認し、semantic partを確立する前にregionを直接geometrizeしたため、Kyoko/Radenで巨大な矩形・カプセルの山へ崩壊した。2nd Cycleではこの失敗を繰り返さない。

現在の本番標準は **Minimalizer 2.0**。ZeroBaseは開発・比較経路であり、Phase 15をPASSするまで本番標準へ切り替えない。

## 2. 仕様の優先順位

実装判断では次を優先する。

1. 現在のユーザー指示
2. この `AGENTS.md`
3. `docs/zerobase/ZEROBASE_2ND_CYCLE_DESIGN.md`
4. 現在Phaseの `docs/zerobase/PHASE*_2ND_CYCLE_*.md`
5. 現在の実装・テスト・stage artifacts
6. その他の旧設計書・試作メモ・外部生成ドキュメント

旧Claude設計書などがこの順序と衝突する場合、**旧文書を根拠にcanonical architectureを変更しない**。

## 3. 絶対に守る設計原則

### 3.1 Semantic-first

処理順は原則として次の通り。

`Subject Extraction → Semantic Parts → Structural Graph → Region-to-Part Binding → Major Mass → Importance/Omission → Palette → Part-aware Geometry → Semantic Composition → Style Simplification`

**semantic partを確立する前に、小領域吸収・細部削除・汎用geometrizationを行ってはならない。**

### 3.2 Evidence, not truth

alpha、rembg、RTMLib、MediaPipe、segmentation、pose、edge、color heuristic等は **Evidence** である。

- confidenceとprovenanceを保持する
- analyzerをground truth扱いしない
- analyzerに最終描画権限を与えない
- unsupportedな領域は `unknown` / `unbound` を許容する
- 不確かなEvidenceを無理に既知partへ割り当てない

### 3.3 生成AIによる可視画像生成は禁止

禁止:

- Stable Diffusion系
- img2img
- ControlNetによる画像生成
- LoRAによる画像生成
- Generative Fill
- 欠損部の生成補完
- 外部生成画像API
- その他、入力に存在しない可視内容を生成・描き足す処理

許可:

- segmentation
- pose / keypoint detection
- face landmark detection
- foreground extraction
- edge / line / region analysis
- その他の**解析専用**ML/NN

したがって `torch` / `onnxruntime` / `mediapipe` / `rembg` 等を一律禁止してはならない。解析モデルはEvidence生成に限り使用できる。

### 3.4 Visible outputは決定論的

最終可視出力はMinimalizerの決定論的ロジックで生成する。同一入力・同一config・同一producer/modelで、mandatory stage artifactsは再実行SHA一致を目標とする。

### 3.5 Fail-local

最初に壊れたPhaseを直す。後段の特例処理で上流の失敗を隠してはならない。

例:

- subject maskが壊れている → Phase 3を直す
- face/hair/arm分解が壊れている → Phase 4を直す
- part relationが壊れている → Phase 5を直す

### 3.6 Visual FAILは数値PASSに勝つ

必須visual QAがFAILなら、そのPhaseはFAIL。IoU、coverage、region count、palette metric等だけでPASSにしてはならない。

## 4. 現在のPhase状態

作業開始時に必ずcanonical docsとGit HEADを再確認すること。手順書作成時点の状態は以下。

- Phase 1: KEEP
- Phase 2: KEEP / contract hardening
- Phase 3 Canonical Subject Extraction: **CLOSED / PASS**
- Phase 4 Semantic Part Decomposition: **CLOSED / PASS**
- Phase 5 Structural Layout Graph: **CLOSED / PASS**
- 次のcanonical step: **Phase 6 Region-to-Part Binding**

Phase 4の確定仕様にはRTMLib WholeBody 133点保持、face68、source-color fallback、optional MediaPipe hair guardが含まれる。これらを旧設計へ戻してはならない。

Phase 5の確定仕様はPhase 4 maskをSHA照合付きread-only入力として扱い、anchor、attachment/spatial/containment/overlap/surrounding relationと、十分なEvidenceがある場合のみfront-behind relationを構築する。髪全体と顔の前後は、前髪/後髪massへ分割されるまでは未確定のまま保持する。Radenの`held-linear` accessoryはarm candidateを優先する。Phase 5でmaskを描き換えて関係失敗を隠してはならない。

## 5. Stage-visibleは必須

Phase 3以降、各Phaseは最低でも次を出力する。

- `stage.json`
- `preview.png`
- `metrics.json`
- Phase固有のmask/map/overlay等

保存先:

`artifacts/zerobase2/<case_id>/phase_<NN>/`

persistent diagnostics:

`docs/zerobase/diagnostics/phase<NN>/<case_id>/`

**自身のpreviewを生成できないPhaseはCLOSEDにしてはならない。**

## 6. Diagnostic corpus

用途を混同しない。

- **Diagnostic-2: Kyoko / Raden**
  - 全アルゴリズム変更で最短フィードバック
  - mandatory stage画像を毎回確認
- **Approved-18**
  - 主要設計変更の中規模回帰
- **Approved-78**
  - Phase 14以降の正式Calibration / Final Gate
  - SHA bindingとdeterministic replayを維持

禁止:

- Diagnostic-2だけに合わせたthreshold tuning
- Approved-78の数値だけを改善するobjective tuning
- visual FAILをmetric PASSで上書き

## 7. Manual overrideの位置づけ

manual mask、remove-id、face bbox等を**デバッグ・診断・緊急override**として持つことは可能。

ただし、それらをcanonical production workflowの主経路にしてはならない。通常利用は1つのミニマル化操作で完結する方向を維持する。

## 8. API / 依存の確認

新しい外部APIやライブラリ関数を使う前に、実在を確認する。

- ローカル環境なら `inspect.signature` / import /最小実行
- 公式ドキュメントが必要なら一次情報を優先
- 確認結果は必要に応じてphase docまたはAPI確認記録へ残す

「存在しそう」で関数・引数を発明しない。

依存追加時は、既存環境・requirements・production boundaryへの影響を確認する。解析ML依存を「生成AIだから禁止」と誤分類しない。

## 9. Git / 外部連携の明示検索ルール

GitHub、Google Drive、RDC、Railway等を使う作業で「利用できない」「見つからない」と結論する前に、対象連携を**明示検索＋最小実操作**する。

ローカルcontainerや `/mnt/data` の確認だけで、外部連携が利用不能と判断してはならない。

Git操作では:

1. `git status --short --branch`
2. `git rev-parse HEAD`
3. `git fetch/pull` が必要か確認
4. ユーザー変更を上書きしない
5. commit前に `git diff --check`
6. push後に local HEAD == origin branch を確認

## 10. テストの原則

変更したPhaseには最低限:

- pure/synthetic unit tests
- Diagnostic-2 real-image run
- mandatory visual artifact確認
- identical rerun SHA確認
- relevant regression suite

を行う。

可能なら既存のmerge-readiness scriptを使用する。

既存の失敗がある場合、今回変更による回帰かbaseline問題かを分離して記録する。

## 11. チューニングの原則

thresholdやweightを変更するときは:

1. 現象をstage imageで特定
2. first-bad-stageを決める
3. 仮説を書く
4. 変更は可能な限り1要因ずつ
5. before/after artifactを残す
6. Diagnostic-2以外への一般化を確認

構造的な欠陥をobjective weight調整で隠さない。

## 12. Claude旧設計から採用してよい考え

以下は積極的に再利用してよい。

- stage分割と中間成果の永続化
- `--from-stage` / `--to-stage` 的な部分再実行思想
- source/config/upstream/code hashによるcache binding
- synthetic test
- API実在確認
- debug画像
- deterministic replay
- 設計変更とコード変更の同期
- tuning / decision log
- pure algorithmとI/O orchestrationの分離

ただしZeroBaseのPhase順序とsemantic-firstを壊す形では採用しない。

## 13. Claude旧設計から採用してはいけない考え

- ニューラル推論全般の禁止
- corner flood-fillを人物foregroundのcanonical主経路にする
- SLIC/region simplificationをsemantic decompositionより先に行う
- 小さい/細いだけを理由にidentity featureを消す
- semantic stageで目・口等のEvidence自体を早期破棄する
- manual remove-idをproduction主経路にする
- 全part共通の単一geometry処理へ戻す
- Kyoko 1枚中心の受入判定
- metric-only gate
- GitHub Actionsを前提に新workflowを増やす
- 別 `src/minimizer/` プロジェクトをゼロから作り直す
- 新規v1/v2タグ計画で現行履歴を上書きする

## 14. Phase完了報告

PhaseをCLOSEDにするときは、最低限以下を記録する。

- status: `CLOSED / PASS` または `HOLD`
- 実装内容
- Diagnostic-2 visual QA
- mandatory artifact paths
- deterministic SHA
- test counts
- regression/gate結果
- commit SHA
- next canonical step

Drive診断ミラーが運用中なら、Phaseごと・caseごとにmandatory画像を反映する。
