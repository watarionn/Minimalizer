<!-- Canonical Google Doc: https://docs.google.com/document/d/1FQYkX0GgXQU0Owpno7svVMjlToufsE5h0yu2_Y34-J8/edit -->

# Minimalizer ZeroBase 2nd Cycle 設計書

Status: DESIGN v1 / implementation-ready

対象: Minimalizer ZeroBase。Phase 1〜2を維持し、Phase 3以降を人物構造優先で再設計する。全体は15工程とする。

## 0. 背景と再設計理由

1st CycleはApproved-78の数値Gateを通過した一方、Kyoko/Radenの実画像では人物構造が巨大な矩形・カプセルへ崩壊した。原因はforeground coverageを人物理解と誤認し、semantic partを確立する前にregionを直接geometrizeしたこと、さらにIoU/foreground-ratio中心の評価が視覚的破綻を検出できなかったことにある。

2nd Cycleでは「人物を意味構造として理解し、その構造を保ったまま削る」を中心原則とする。下流工程で上流の構造欠落を補正する設計は禁止する。

### Step 0. Production Safety Rollback（工程外・最優先） [CLOSED]

Status: CLOSED。本番標準ルートをMinimalizer 2.0へ復帰済み。標準ブラウザ経路は `/api/v2/minimalize`、`?localWorker=1` はLocal Workerの `/api/v2/minimalize` を試行する。ZeroBase専用 `/api/zerobase/minimalize` は開発・比較用として保持する。production rollback code SHA `d0a88ccf45704ebbf0a98bf639e4a699aaf5f94d`、Railway production deployment `092d34c3-7807-4bcf-9ced-b74306c74d7e`。focused web/cutover tests 31 passed、production health PASS、Kyoko production V2 smoke HTTP 200 / 40 shapes。2nd CycleがPhase 15をPASSするまでZeroBaseを標準ルートへ再切替しない。

## 1. 設計原則

Semantic-first: foregroundの存在ではなく、head/hair/face/torso/arms/accessories/clothing masses等の意味構造を先に確立する。

Evidence, not truth: alpha、rembg、pose、segmentation、edge等はEvidenceとして扱い、provenanceとconfidenceを保持する。解析モデルに最終描画権限を与えない。

Deterministic visible output: 最終画像はMinimalizerの決定論的ロジックのみで描画する。Stable Diffusion、img2img、Generative Fill、欠損補完などの生成処理は禁止する。

Stage-visible: Mandatory stage renderingはPhase 3から開始し、以後すべてのPhaseでPNG previewを保存する。最終画像だけを見て判定する運用は禁止する。

Fail-local: 破綻が最初に現れたPhaseを修正対象とし、後段の特例処理で隠さない。

Visual gate overrides metric optimism: 数値がPASSでも必須visual QAがFAILならPhaseはFAILとする。

## 2. テストコーパス階層

Diagnostic-2: KyokoとRaden。全アルゴリズム変更で必ず全stage画像を生成し、最短フィードバック用に使う。今回の破綻を再発させないための固定診断ケースとする。

Approved-18: 主要な設計変更ごとの中規模回帰。人物構造、幾何化、省略傾向の横展開を確認する。

Approved-78: Phase 14以降の正式Calibration/Final Gate。SHA bindingとdeterministic replayを維持する。

禁止事項: Diagnostic-2だけに合わせた閾値調整、Approved-78の評価値だけを改善するobjective tuning、見た目FAILを数値PASSで上書きする運用。

## 3. Stage Artifact Contract

保存ルートは artifacts/zerobase2/<case_id>/phase_<NN>/ とする。Phase 3以降は最低でも stage.json、preview.png、metrics.json を必須とし、必要に応じてoverlay.png、mask.png、labels.png、removed.pngを追加する。

stage.jsonにはsource SHA-256、config hash、producer/version、入力artifact SHA、出力artifact SHA、coordinate space、determinism seed policy、evidence provenanceを記録する。

preview.pngは同一caseでcanvas sizeとorientationを固定する。overlay系は元画像と比較可能な位置合わせを崩さない。Semantic mapの色キーは全caseで固定する。

各Phaseは自身のpreviewを生成できなければCLOSEDにできない。データ構造だけ実装して画像化を後回しにすることは禁止する。

## 4. Phase Map

Phase 1〜2はKEEP。Phase 3〜15を2nd Cycleとして再設計する。Phase 3〜12が画像生成本体、Phase 13が可視化統合、Phase 14が評価再設計、Phase 15が本番統合である。

### Phase 1. Foundation [KEEP]

目的: schema、coordinate space、canonical serialization、deterministic replay、artifact bindingを維持する。

入力/出力: analyzer以前の共通モデルとcanonical metadata。

再利用: minimalizer_zerobase/core と既存serialization/coordinate資産を優先再利用する。

PASS: 同一入力・同一configからcanonical JSONが完全一致し、schema migrationが明示されること。

### Phase 2. Analysis Foundation [KEEP + CONTRACT HARDENING]

目的: alpha/rembg/segmentation/pose/edge等を統一Evidence contractへ格納する。

入力: source image。出力: spatial evidence、confidence、provider/model、provenance。

可視化: mandatoryではないがspatial evidenceを持つanalyzerには02_evidence_overlay.pngを生成可能にする。Mandatory stage renderingはPhase 3から。

PASS: analyzerがground truth扱いされず、image bytesを最終renderへ直接流用せず、provenanceが欠落しないこと。

### Phase 3. Canonical Subject Extraction [CLOSED / PASS]

目的: 背景とsubjectを分離し、人物本体のcanonical mask、bbox、center、scaleを確定する。

主処理: source alphaを最優先。alphaが無い場合のみ許可済み解析Evidenceを融合する。穴埋めや生成補完は行わない。輪郭の孤立ノイズ除去とsmall-hole policyを明示する。

出力: subject_mask、subject_bbox、subject_transform、evidence provenance。

可視化: 03_subject_mask.png、03_subject_overlay.png。

PASS: Kyoko/Radenで髪・腕・持ち物を含む主体輪郭が大きく欠落せず、背景がsubjectへ大量混入しないこと。

失敗時の戻り先: Phase 2 Evidence fusion。下流でmaskを補正しない。

Closure: Diagnostic-2のKyoko/Radenでalphaが約99.68%全面不透明であることを検出し、non-informative alphaを棄却してrembg isnet-animeへ切替。`03_subject_mask.png` / `03_subject_overlay.png` を生成しVisual QA PASS。mask/overlayは再実行SHA一致。Phase 3 tests 4 passed、ZeroBase suite 71 passed。詳細は `PHASE3_2ND_CYCLE_CANONICAL_SUBJECT.md`。

### Phase 4. Semantic Part Decomposition [CLOSED / PASS]

目的: subjectを意味部位へ分解する。最低part setは head、hair、face、neck、torso、left_arm、right_arm、lower_body、major_clothing、accessory/held_object。

主処理: 複数Evidenceを用いたpart hypothesis生成。unknownを許可し、confidence不足を無理に既知partへ割り当てない。

出力: semantic_part masks、part confidence、part hierarchy。

可視化: 04_part_map.png、04_part_overlay.png。Semantic色キーは固定。

PASS: 顔・髪・胴体・腕・主要アクセサリが少なくとも別の意味領域として読めること。Kyokoのゴーグル/ネクタイ、Radenのロッド/長髪等のmajor identity featureがunknown一塊に吸収されないこと。

失敗時の戻り先: Phase 2またはPhase 3。

Closure: Diagnostic-2でRTMLib WholeBody構造、source-color face/hair解析、optional MediaPipe hair guardを統合。Kyokoは髪・顔・首・胴体・左右腕・緑ネクタイを分離、Radenは長髪・顔・胴体・大袖/左右腕・ロッドを分離。Radenで発生した黒髪→黒袖への過剰拡張はPhase 4内で修正した。`04_part_map.png` / `04_part_overlay.png` は再実行SHA一致。Phase 4 tests 4 passed、ZeroBase suite 75 passed。詳細は `PHASE4_2ND_CYCLE_SEMANTIC_PARTS.md`。

### Phase 5. Structural Layout Graph [NEW CORE]

目的: semantic partsを人物構造として接続し、位置・接続・前後・包含関係を定義する。

主処理: head-above-torso、arm-attached-to-torso、hair-around-head、accessory-attached-to-part、front/behind、left/right等をgraph relationとして保持する。

出力: part graph、anchors、relation confidence。

可視化: 05_structure_graph_overlay.png。anchorとrelationを元画像上へ描画する。

PASS: 人物の主要骨格関係がgraphとして成立し、孤立major partや循環したocclusion relationがないこと。

失敗時の戻り先: Phase 4。

### Phase 6. Region-to-Part Binding [REDESIGN]

目的: superpixel/regionをsemantic partへ帰属させ、色が似ているだけの背景・別部位統合を防ぐ。

主処理: geometry overlap、part mask、graph relation、color evidenceを使ってbindingする。confidence不足はunboundのまま保持できる。

出力: region records with semantic_part_id、binding confidence、boundary evidence。

可視化: 06_region_binding.png、06_unbound_overlay.png。

PASS: 顔色regionが背景へ、髪色regionが服へ等のcross-part誤結合がmajor areaで発生しないこと。

失敗時の戻り先: Phase 4〜5。

### Phase 7. Major Mass Reconstruction [REDESIGN]

目的: 細かいregionを意味を保ったmajor massへ統合する。

主処理: part内mergeを基本とし、前髪、後髪、顔、上半身服、ネクタイ、ゴーグル、ロッド等の大塊を形成する。part境界を越えるmergeには明示relationが必要。

出力: semantic masses、mass hierarchy、mass silhouette。

可視化: 07_mass_blocks.png、07_mass_outline_overlay.png。

PASS: この段階の塗りつぶしだけで人物のポーズと主要特徴が読めること。ここで人物性が読めなければPhase 8以降へ進めない。

失敗時の戻り先: Phase 6。

### Phase 8. Importance / Omission Policy [REDESIGN]

目的: 何を残し何を捨てるかをsemantic importanceとして決定する。

主処理: silhouette contribution、part role、identity contribution、visual salience、redundancyを分離評価する。小さいという理由だけでidentity featureを削除しない。

出力: keep/protect/prune候補、importance score breakdown、omission reason。

可視化: 08_importance_heatmap.png、08_pruned_masses.png、08_removed_overlay.png。

PASS: major silhouette、顔/髪の分離、特徴アクセサリ、主要色塊がprotectされ、削除対象が主に冗長fragmentへ集中すること。

失敗時の戻り先: Phase 7またはimportance rule。

### Phase 9. Palette Consolidation [REUSE + REDESIGN]

目的: semantic part間の識別性を壊さず色数を削減する。

主処理: part-aware representative color、near-color merge、contrast guard、skin/hair/clothing identity guard。影やシワ由来の色差は優先的に統合する。

出力: canonical palette、material assignment、merge rationale。

可視化: 09_palette_preview.png、09_palette_strip.png。

PASS: 元画像の主要色関係とpart識別が保たれ、shading色が独立primitiveを増殖させないこと。

失敗時の戻り先: palette ruleまたはPhase 8 protect情報。

### Phase 10. Part-Aware Geometrization [MAJOR REDESIGN]

目的: semantic part/massごとに適切なprimitive候補を生成し、人物性を保った幾何化を行う。

主処理: 全regionへ同じrectangle/capsuleを当てる方式を禁止する。face/hair/torso/arm/accessory/rod/tie等でcandidate familyとcomplexity budgetを変える。各massに複数candidateを生成する。

候補例: polygon、rounded polygon、ellipse、capsule、oriented rectangle、tapered strip、polyline ribbon等。candidateは必ずsource massとsemantic partへbindingする。

出力: primitive candidates、candidate costs、selected primitive set。

可視化: 10_candidate_grid.png、10_selected_primitives.png。

PASS: Kyoko/Radenで巨大矩形・カプセルの連鎖へ崩れず、頭・髪・胴体・腕・特徴物の形状差が残ること。

失敗時の戻り先: Phase 7 mass形状、Phase 8 importance、またはpart-specific candidate generator。

### Phase 11. Semantic Composition [REDESIGN]

目的: selected primitivesを人物として再合成し、z-orderとoverlapをsemantic graphに従わせる。

主処理: hair in front/behind face、accessory on head/torso、arm in front of clothing等をgraph relationから解決する。描画順をregion id順だけで決定しない。

出力: composed vector scene。

可視化: 11_composed_minimal.png、11_zorder_overlay.png。

PASS: primitive単体では正しくても合成で顔や手が隠れる等の破綻がないこと。

失敗時の戻り先: Phase 5 relationまたはcomposition policy。

### Phase 12. Style Constraint & Simplification Pass [REDESIGN]

目的: 人物性を壊さず、Approved styleに向けて最後の単純化を行う。

主処理: micro-shape prune、near-collinear merge、shape count budget、oversized primitive penalty、thin-fragment penalty、face-collapse guard、identity-feature guard。

出力: final deterministic vector scene。

可視化: 12_final.png、12_removed_shapes_overlay.png、12_before_after.png。

PASS: Phase 11からの単純化でsemantic partの読みやidentity featureが消えないこと。最終見た目を人間が同一人物のミニマル化として認識できること。

失敗時の戻り先: Phase 8またはPhase 10〜11。

### Phase 13. Stage Visualizer / Debug Board [NEW MANDATORY]

目的: どのPhaseで最初に破綻したかを一目で特定できる統合QA面を作る。

主処理: input、03 subject、04 parts、05 graph、06 binding、07 masses、08 prune、09 palette、10 primitives、11 composed、12 finalを同一case boardへ並べる。

出力: 13_debug_board.png、13_stage_index.json。

PASS: Diagnostic-2の各caseで全mandatory stageが欠落なく並び、最初の視覚破綻点をstage idで指摘できること。

運用ルール: Debug Boardを確認せずにPhase 14の数値Gateだけで品質判断してはならない。

### Phase 14. Evaluation Redesign & Calibration [MAJOR REDESIGN]

目的: 数値PASSと視覚FAILの乖離を防ぐ評価系を作る。

評価軸: silhouette preservation、part layout consistency、major color mass consistency、identity feature retention、oversized-block penalty、fragmentation penalty、face/hair/torso collapse、primitive economy、determinism。

human visual QAを正式Gateへ含める。最低判定は same-subject recognizability、pose readability、major-feature retention、minimal-style consistency、catastrophic-block failure absence。

出力: case evaluation JSON、14_eval_sheet.png、corpus summary。

PASS: Diagnostic-2がvisual PASS、Approved-18が回帰PASS、Approved-78が正式Gate PASS。数値とhuman QAが矛盾した場合はFAIL側を採用する。

失敗時の戻り先: 最初に破綻したPhaseへ戻る。Phase 14でrender algorithmへ例外処理を追加しない。

### Phase 15. Production Integration & Final Gate [REDESIGN]

目的: ZeroBase 2nd Cycleを安全に本番標準へ昇格する。

条件: full deterministic replay、Diagnostic-2/Approved-18/Approved-78 PASS、human visual QA PASS、Docker/build PASS、production smoke PASS、rollback PASS。

本番切替はfeature flagまたは明示route switchで行い、Minimalizer 2.0 rollback pathを保持する。最初の切替コミットで旧実装を削除しない。

可視化: 15_production_compare_board.png。開発出力と本番出力のpixel/metadata一致を確認する。

PASS: 実際のブラウザ標準ボタンからDiagnostic-2相当のreal image smokeを行い、route、artifact、見た目を確認して初めてMIGRATION CLOSEDとする。

## 5. Failure Localization Rules

First-bad-stage rule: Debug Board上で最初に壊れたPhaseをroot cause候補とする。後続Phaseの見た目補正で隠さない。

Upstream contract rule: Phase Nの入力が既に破綻している場合、Phase Nを修正対象にしない。N-1以前へ戻る。

No silent fallback during evaluation: Calibrationでは2.0 fallbackを混在させない。fallbackはproduction safety専用とし、評価結果にZeroBase成功として計上しない。

No hidden quality tuning: Gate閾値変更時は理由、影響case、before/after boardを残す。

## 6. 2nd Cycleの主要データモデル

SemanticPart: part_id、role、mask_ref、bbox、confidence、parent_id、evidence_refs。

PartRelation: source_part、target_part、relation_kind、confidence、evidence_refs。

SemanticMass: mass_id、part_id、region_ids、mask_ref、silhouette、importance、protected_reason。

PrimitiveCandidate: candidate_id、mass_id、part_id、primitive_type、parameters、cost_breakdown。

StageManifest: case/source/config/producer SHA bindingと全artifactのhashを保持する。

## 7. 既存資産の扱い

KEEP候補: core serialization/coordinates、evidence contracts、Approved-78 manifest/binding、deterministic replay、paletteの一部、production boundary、既存rembg解析基盤。

REWORK候補: scene fusion、region reconstruction、importance、geometrizer、semantic composer、optimizer、MigrationGate/FinalQualityGate。

REFERENCE ONLY: 1st Cycleの直接SLIC-to-primitive経路。比較対象として保持するが、2nd Cycleのcanonical production pathにはしない。

## 8. 実装順序

最初の実装マイルストーンはPhase 3〜7とする。Diagnostic-2で03〜07のstage画像を連続生成し、07_mass_blocksの時点で人物として読めることを確認するまでPhase 8へ進まない。

次にPhase 8〜12を実装し、同じDebug Board上で「どの単純化処理が人物性を落とすか」を追う。Phase 13を常時更新しながら開発する。

Phase 14で初めてApproved-78全件の正式Calibrationを行い、Phase 15でproduction integrationへ進む。

## 9. Definition of Done

2nd Cycle完成条件は、15工程が実装済みであることではない。Kyoko/Radenを含む必須caseについて、Phase 3からPhase 12までの画像が連続保存され、最終出力が人物構造・主要色塊・identity featureを保ったミニマル画像として視覚PASSし、その結果を評価系が正しくFAIL/PASS判定できることを完成条件とする。

最終的なMIGRATION CLOSEDは、Phase 15のproduction smokeとrollback確認まで完了した時点だけで付与する。

## 10. 直近の次工程

Step 0として本番標準をMinimalizer 2.0へ安全に戻す。その後Phase 3 Canonical Subject Extractionの2nd Cycle実装を開始し、Kyoko/Radenの03_subject_mask / 03_subject_overlayを最初の可視化チェックポイントとする。

