# Minimalizer ZeroBase 2nd Cycle — Codex開発手順書

版: 2026-09-28 / Claude手順書再構成版

この文書は、Claudeが作成した旧 `Minimizer` 手順書のうち、再現性・デバッグ性・実装作法の良い部分を残し、現在の **Minimalizer ZeroBase 2nd Cycle** のcanonical architectureへ合わせて再構成したもの。

## 1. 目的

Codexが以下を壊さずにMinimalizerを継続開発できることを目的とする。

- Semantic-first
- Evidence / render authority分離
- 生成AIによる画像生成禁止
- 解析MLの許可
- deterministic visible output
- stage-visible debugging
- fail-local
- visual QA優先
- Diagnostic-2 → Approved-18 → Approved-78 の評価階層
- Minimalizer 2.0 production safety boundary

## 2. 作業開始時チェック

毎runの最初に行う。

1. `AGENTS.md` を読む
2. `docs/zerobase/ZEROBASE_2ND_CYCLE_DESIGN.md` を読む
3. 現在Phaseのclosure docを読む
4. `git status --short --branch`
5. `git rev-parse HEAD` と `origin/main` の関係を確認
6. Diagnostic-2の最新stage artifactsを確認
7. 次のcanonical Phase以外へ勝手に飛ばない

外部連携が必要な場合はGitHub / Drive / RDC / Railway等を明示検索する。ローカルファイルが見えないことを、外部連携の不在と同一視しない。

## 3. 現在のcanonical state

手順書作成時点:

- Production standard: Minimalizer 2.0
- ZeroBase production standard switch: 禁止、Phase 15まで待つ
- Phase 3: CLOSED / PASS
- Phase 4: CLOSED / PASS
- Phase 5: CLOSED / PASS
- Phase 6: IMPLEMENTED / READY FOR RINKA RE-REVIEW（parent ambiguity inheritance revision 1.1）
- 次: Phase 6 independent re-review（Phase 7へは進まない）

Phase 4ではRadenの2種類の失敗を人間のvisual QAで検出し、Phase 4内で修正済み。

- dark hairがdark sleeveを侵食
- faceが小さく左ズレ

最終Face geometryはRTMLib WholeBody face68を主Evidence、source-color locatorをfallback/diagnosticとしている。

## 4. 正式Phase順序

### Phase 1 Foundation

KEEP。schema、coordinate、canonical serialization、deterministic replay、artifact binding。

### Phase 2 Analysis Foundation

KEEP + hardening。alpha/rembg/RTMLib/MediaPipe/segmentation/pose/edge等をEvidence contractへ格納。

### Phase 3 Canonical Subject Extraction

背景とsubjectを分離。informative alphaのみ採用し、non-informative alphaは解析Evidenceへfallback。

Artifacts:

- `03_subject_mask.png`
- `03_subject_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

### Phase 4 Semantic Part Decomposition

subjectを `head / hair / face / neck / torso / arms / lower_body / major_clothing / accessory / unknown` へ分解。

Artifacts:

- `04_part_map.png`
- `04_part_overlay.png`
- part masks
- `preview.png`
- `metrics.json`
- `stage.json`

### Phase 5 Structural Layout Graph

part間の関係を明示する。

最低関係例:

- head above torso
- face inside/anchored-to head
- hair around head / overlaps face
- left/right arm attached to torso
- accessory attached to head/torso/hand candidate
- front / behind when supported by evidence
- contains / adjacent / attached

重要: 髪全体と顔の前後をPhase 4 display priorityだけで断定しない。前髪/後髪massへ分割されるまではhair/face depthは未確定を許容する。

Output:

- part graph
- anchors
- relation confidence
- evidence refs

Mandatory visual:

- `05_structure_graph_overlay.png`
- `preview.png`
- `metrics.json`
- `stage.json`

PASS:

- major partが孤立しない
- attachmentが人物構造として妥当
- face-inside-head、neck-face、neck-torso、lower-body-torso等のcore relationが欠落しない
- front/behindに循環がない
- unsupportedなfront/behind relationを無理に作らない
- Kyoko/Radenを元画像上のoverlayで人間が読める

FAILならPhase 4へ戻る。Phase 5でpart maskを描き直してPhase 4失敗を隠さない。

### Phase 6 Region-to-Part Binding

region/superpixelをsemantic partへbind。ここで初めてregionがsemantic structureへ正式に接続される。

### Phase 7 Major Mass Reconstruction

part内を中心にregionをmajor massへ統合。07_mass_blocks.png の時点で人物として読めなければPhase 8へ進まない。
### Phase 8 Importance / Omission Policy

silhouette、semantic role、identity contribution、salience、redundancyを分離してkeep/protect/prune。

**面積が小さいだけでは削除しない。**

### Phase 9 Palette Consolidation

part-aware palette。skin/hair/clothing/accentの識別を壊さず、影・シワ由来の色差を圧縮。

### Phase 10 Part-Aware Geometrization

face/hair/torso/arm/tie/rod等でcandidate familyを変える。全regionへ同じ矩形・capsuleを適用しない。

### Phase 11 Semantic Composition

graph relationに従ってz-order / overlapを解決。

### Phase 12 Style Constraint & Simplification

人物性・identity featureを守りながら最終単純化。

### Phase 13 Stage Visualizer / Debug Board

input〜Phase 12を一枚へ並べ、first-bad-stageを可視化。

### Phase 14 Evaluation Redesign & Calibration

Diagnostic-2 visual PASS、Approved-18 regression、Approved-78 formal Gate。human visual QAを正式Gateに含める。

### Phase 15 Production Integration & Final Gate

production smoke、rollback、development/production output consistencyを確認して初めてMIGRATION CLOSED。

## 5. Stage Artifact Contract

Phase 3以降は最低限:

```text
artifacts/zerobase2/<case_id>/phase_<NN>/
├─ stage.json
├─ preview.png
├─ metrics.json
└─ <phase-specific visual/data>
```

`stage.json` には最低限:

- source SHA-256
- input artifact SHA
- config + config SHA
- producer / version
- analyzer/model provenance
- coordinate space
- determinism policy
- output artifact SHA

を含める。

persistent diagnostic snapshot:

`docs/zerobase/diagnostics/phase<NN>/<case_id>/`

## 6. Google Drive診断ミラー

人間が工程画像を見比べるため、Git側のpersistent diagnostic snapshotをGoogle Driveへmirrorする。

Drive root:

`Minimalizer ZeroBase 2nd Cycle / Diagnostics / Phase XX / <case>`

Diagnostics root:

https://drive.google.com/drive/folders/1GBXMgo8OSpK2UfqiKewTKeBTspioKnOP

各caseの診断Docに、少なくともmandatory visualと主要metricsを埋め込む。

Driveはvisual review用。canonical algorithm/specはGitの設計書とphase closure docs。

## 7. 解析AI / 生成AIの境界

### 許可

- rembg
- RTMLib
- MediaPipe
- segmentation
- pose/keypoint
- face landmark
- object/part detection
- edge/line analysis
- classifier

条件:

- Evidence用途
- provenance/confidence保持
- analyzer出力をground truth扱いしない
- visible render authorityを与えない

### 禁止

- Stable Diffusion
- img2img
- ControlNetによる生成
- LoRA生成
- Generative Fill
- inpaintingによる描き足し
- 欠損部生成
- 外部画像生成API

## 8. Claude手順書から引き継ぐ実装作法

### 8.1 stage persistence

途中成果を保存し、特定Phaseだけ再実行できる構造は推奨。既存Phase artifact contractを優先して設計する。

### 8.2 pure logicとI/Oの分離

可能な限り:

- algorithm/data model
- artifact writer
- runner/orchestration

を分離する。現在の `subject/`、`parts/` の構成が参考になる。

### 8.3 API実在確認

新APIは最小import、signature確認、最小実行で確認する。推測でAPIを発明しない。

### 8.4 synthetic tests

real imageだけに依存せず、形の分かるsynthetic fixtureでboundary/graph/geometryを固定する。

### 8.5 cache / artifact binding

source/config/upstream/producer versionをhash bindingできる構造を維持する。

### 8.6 tuning log

threshold変更は現象・仮説・変更・結果・before/after artifactを残す。
## 9. Claude手順書から置き換えるルール

| Claude旧案 | 2nd Cycleでの置換 |
|---|---|
| NN inference禁止 | 解析NNはEvidence用途で許可。生成AIは禁止 |
| corner flood-fill主経路 | informative alpha → approved analysis Evidence |
| segment → simplify → semantic | semantic → graph → region binding → mass reconstruction |
| 小領域/細部を早期吸収 | identity/semantic importance判定後にprune |
| face semanticで目口を即消去 | face Evidenceは保持。省略は後段で判断 |
| manual remove-id主経路 | diagnostic override。production主経路にしない |
| generic Gaussian geometry | part-aware candidate geometry |
| Kyoko単体受入 | Diagnostic-2 → Approved-18 → Approved-78 |
| metric中心 | visual FAIL優先 |
| GitHub Actions想定 | local/RDC gate優先。Actionsを増やさない |
| 新規 `src/minimizer/` | 現行Minimalizer repoを継続 |
| 新v1/v2タグ | 既存履歴と現行Phase運用を優先 |

## 10. 変更1件の標準手順

1. canonical phaseとfailure locationを確認
2. Git status / HEADを確認
3. 既存資産を明示検索
4. 最小仮説を立てる
5. pure implementationを追加/修正
6. synthetic unit test
7. Diagnostic-2実行
8. mandatory stage imagesを目視
9. FAILならfirst-bad-stageへ戻る
10. identical rerun SHA確認
11. relevant regression
12. `git diff --check`
13. persistent diagnostic snapshot更新
14. phase doc / design doc更新
15. commit / push
16. local HEAD == origin確認
17. Drive diagnostic mirror更新
18. HANDOFF更新

## 11. Phase 5実装時の特別ルール

次に実装するPhase 5は、Phase 4 maskを**変更しない**。

### Data model候補

```text
PartAnchor
- anchor_id
- part_id
- kind
- x/y normalized or canonical coordinate
- confidence
- evidence_refs

PartRelation
- source_part
- target_part
- relation_kind
- confidence
- evidence_refs
```

relation kind候補:

- above / below
- left_of / right_of
- inside / contains
- attached_to
- overlaps
- in_front_of / behind
- surrounds

### Fail conditions

- face/head/torso/major armが孤立
- arm attachmentがtorsoから離れる
- accessory attachmentが無根拠
- front/behind cycle
- Phase 4 maskをPhase 5で描き換えて辻褄を合わせる

### Mandatory visual

元画像 + part boundary + anchors + relation arrowsを重ねる。

色・記号は全caseで固定する。

## 12. Testing hierarchy

### Focused

変更moduleのunit tests。

### Phase suite

`tests/zerobase` の関連範囲。

### Integration

既存 `scripts/Test-MergeReadiness.ps1` 等、repoの現行Gateを優先。

新しいActions workflowを作って代替しない。

## 13. Production safety

Phase 15以前:

- production standard = Minimalizer 2.0
- ZeroBase = development/comparison
- production route switch禁止
- 2.0 rollback pathを削除しない

Calibration中は2.0 fallbackをZeroBase成功として数えない。

## 14. 完了報告テンプレート

```text
Phase XX: CLOSED / PASS | HOLD

Implementation:
- ...

Diagnostic-2:
- Kyoko: PASS/FAIL +要点
- Raden: PASS/FAIL +要点

Artifacts:
- ...

Determinism:
- SHA ...

Tests/Gates:
- focused: N passed
- ZeroBase: N passed
- integration: PASS/FAIL
- git diff --check: PASS/FAIL

Commit:
- <full SHA>

Production:
- unchanged / intentionally changed in Phase 15 only

Next:
- Phase XX ...
```

## 15. Codexが止まるべき条件

質問やHOLDが必要なのは主に以下。

- canonical設計同士が矛盾している
- 生成AIを使わなければ達成できない変更要求
- production切替が必要だがPhase 15 Gate未達
- user-owned変更を安全に保持できない
- required evidence/provenanceが取得不能で、unknown/fail-closedでも続行できない

それ以外は、既存資産を明示検索して可能な範囲まで自律的に進める。
