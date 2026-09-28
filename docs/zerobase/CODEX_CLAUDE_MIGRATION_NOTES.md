# Claude手順書 → ZeroBase 2nd Cycle Codex手順書 対応表

この文書は、Claude作成の `01_requirements.md`〜`05_implementation_plan.md` / `AGENTS.md` から、何を残し何を置き換えたかを示す。

## KEEP

- stage分割
- intermediate artifact永続化
- partial rerunの考え方
- deterministic replay
- source/config/upstream/code binding
- synthetic tests
- API実在確認
- debug画像
- pure algorithmとI/O分離
- tuning/decision log
- エラーを後段へ流さない

## MODIFY

### offline

旧案: 実行時通信を全面禁止。

新案: production runtimeのsilent dependency/model fetchは避ける。モデル取得や依存導入はprovisioningとして明示・監査する。解析モデル自体は禁止しない。

### manual workflow

旧案: remove-id / mask / face bboxをv2主経路。

新案: diagnostic/manual overrideとして保持可能。canonical production workflowの主経路にはしない。

### palette metric

旧案: ΔEや使用色数中心。

新案: part-aware palette + identity guard。ΔE等はdiagnostic metricとして利用可能。

### stage resume

旧案の `--from-stage` / `--to-stage` は思想として有用。現行artifact contract・runner構造へ合わせて実装する。

## REJECT

### neural inference ban

理由: 現行Phase 3/4がrembg、RTMLib、MediaPipe等をEvidenceとして正式使用しているため。

### simplify-before-semantic

理由: 1st Cycle崩壊の根本原因を再導入するため。

### corner flood-fill as canonical foreground

理由: Kyoko/Radenのような背景込み画像でPhase 3 Evidence fusionより弱い。

### early face blanking

理由: face68等のEvidenceを後段importance/style判断より前に失うため。

### area/thin-first deletion

理由: small identity featuresを消すため。

### manual-first production

理由: Minimalizerの1ボタンproduction方向と矛盾。

### generic geometry

理由: Phase 10 Part-Aware Geometrizationと矛盾。

### Kyoko-only tuning

理由: Diagnostic-2 / Approved-18 / Approved-78 hierarchyと矛盾。

### metric-only acceptance

理由: visual FAIL overrides metric optimismルールと矛盾。

### GitHub Actions default CI

理由: 現行運用はActions依存削減。local/RDC Gateを優先。

### new standalone project/version history

理由: 現行Minimalizer repo、2.0 production、ZeroBase historyを継続する必要がある。
