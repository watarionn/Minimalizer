# MinimalizerLocal 統合キャンペーン現況・保存方針

更新日: 2026-11-10

この文書は、Lane A（実画像品質）とLane B（L04/L05/L07統合）の現在地を
一枚に固定するための source-free 台帳である。過去の実験結果を削除したり、
正式ゲートを自動昇格したりするものではない。

## 正本と現在の作業点

| 対象 | SHA / 状態 |
|---|---|
| 最新 `origin/main` | `54654bfac80550a4fe565de694c39d30b47b5703` |
| Lane A PR #449 | Draft / `research/local-l02-class32-topology-palette-shadow-20261102`（GitHub remote headを正本としてreadback） |
| Lane B PR #451 | 過去のB成果を保持。Aの品質候補をBへ混ぜない |
| A L02 / Phase4 | `HOLD` / `FAIL`（キャンペーン正式昇格なし） |
| Phase5 | `NO_GO`（Phase4独立PASS前は禁止） |
| L04 handoff | `false` |
| Golden / production | `HOLD` / `NO_GO` |

2026-11-10の読み取り専用B再検証では、PR #451 head
`c593b46c53c28127b08d74d2ce733045495b5577` に対してL04/L05/L07/Workerの
focused suiteが `46 passed`。Service Worker generation pin、shell-only cache、
no-store route、offline shell fallback、L05 concurrency契約を静的に確認した。
これはBのsource/runtime QAであり、production反映・実機iPhone受入・L04正式三点
セットの完成を意味しない。L07監査自身も `L07_actual_live_iphone=NOT_TESTED`、
`L08_release=NOT_APPROVED` を返している。

## AとBの役割

```text
署名済み元画像
      │
      ▼
A: source-only推論 → owner/腕/下着/遮蔽の意味評価 → Phase4
      │                         │
      │ Phase4 PASS のみ         └─ FAIL/HOLDなら候補を凍結して停止
      ▼
Phase5 exact replay
      │
      ▼
B: Stage8三点照合 → SVG/Chromium/予算 → PWA/Worker/障害系
      │
      ▼
Golden承認 → 本番反映 → 実機iPhone受入
```

BはAの画像品質を判定する担当ではなく、Aが正式に渡した結果を壊さず表示・
配信・復旧できるかを確認する担当である。したがって、Bが機能的にPASSでも、
AのPhase4がFAILなら完成にはならない。

## 保持するもの

次のものは、後からSHA・来歴・再現条件を確認するため必ず保持する。

- 署名済みH04/H06/H08元画像のSHA対応表と、候補出力のfreeze receipt。
- source-only推論コード、observerのモデル／重み／class-map／出力SHA、負例テスト。
- Phase4独立評価receipt、候補SHA、source SHA、評価者・時刻・署名の結び付き。
- H04/H06/H08それぞれのPhase4、Phase5、Stage8、L04三点セットのsource-free台帳。
- L04の元画像・Stage8 JSON・展開SVG・manifest・gate resultの相互SHA。
- L05/L07の実際のHTTP、429/Retry-After、fallback、offline復帰、PC/iPhone記録。
- PR、コミットSHA、テスト結果、HOLD/FAIL/NO_GOの理由。

原画像、マスク、NPZ、座標、比較画像はGitHubへ入れず、承認済み非公開Driveに
保持し、既存のreadback記録とSHAを残す。

## 参照のみとして隔離するもの

古いRun、候補NPZ、既知例への後合わせ、label付きpost-score、旧Stage8、旧SVG、
旧cap試行は削除せず、`historical / superseded / not-formal` として保管する。
これらを新しい候補の推論入力や正式品質証拠には戻さない。

特に次は正式対象外である。

- 現在のH08 `H08_PHASE4_MATERIALIZED_RECEIPT.json`（`phase4=FAIL`）。
- `formal-triple-preserving-package-v2`（H04一式がなく、H06/H08のmanifestも不足）。
- `1887` capで作られた、正式方針の確認がない旧L04候補。
- 独立評価結果の意味を示す資料であっても、現在の候補SHAと署名を結ばないJSON。

## 次に実行する工程

具体的な順序と、局所修正を再開しない条件は
`docs/research/LOCAL_L02_DEVELOPMENT_METHOD_RESET_20261110.md`を正本とする。
現時点の次作業は、旧候補を正式入力から隔離したうえで、H04/H06/H08の意味クラス別
失敗表を一枚に固定し、三例同時の全身outerwear候補を独立レビューへ渡すことである。
G0台帳と候補の診断値は
`docs/research/LOCAL_L02_G0_CANONICAL_INVENTORY_20261110.md` に固定した。
Phase4が全ケースで独立PASSになった場合だけPhase5 exact replay、L04正式三点セット、
Golden、本番、実機iPhone受入へ進む。

現時点では、新しいB実装や本番変更を行わない。正式に足りないのは、追加の実験数
ではなく、現在候補に束縛されたPhase4 receiptと、Phase4後に作るH04を含むL04三点セットである。

なお、H06/H08の数画素候補では根本品質に届かないことが判明したため、開発方式を
全体owner再構成へ切り替えた。開発サイクル、候補にしない変更、完了判定は
`docs/research/LOCAL_L02_DEVELOPMENT_METHOD_RESET_20261110.md`、実装土台と
残差の詳細は `docs/research/LOCAL_L02_SCALE_RESET_20261110.md` を正本とする。

