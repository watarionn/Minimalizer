# MinimalizerLocal 完成計画 v1（提案）
**2026-10-15 / status: ADOPTED, NOT RELEASE APPROVAL**

## 完成の定義

MinimalizerLocal はユーザー専用の private-HTTPS PWA + LocalWorker。Public/C08 は別の配布経路・リリース判定とする。完成とは「画質が良さそう」という研究報告ではなく、同じ署名済み入力で再現可能な高品質成果が、実機iPhoneから安全・安定に得られ、人間が受け入れたことを意味する。

**品質上の必須条件**
- 画像が手本と同じ程度に**人間から認識できるシルエット、頭・髪・肩・左右の腕、衣装、アクセサリ**を保持する。
- 元画像にない可視画素の生成・描き足し／img2img・inpainting／全身スキン色の不正なベース塗りは禁止。原画像、署名済みマスクは不変。
- 既定で目・鼻・口・眉は描画しない。顔の輪郭・髪・肌の参照情報は消さない。
- 「顔・衣服の色領域」「ジオメトリ」「表示順」「ソースStage8予算」「圧縮/展開SVG予算」を別々に証明。品質FAILを数値PASSで打ち消さない。
- 正式Golden承認と実機iPhone受入を自動で代行しない。素材・承認票は非公開Drive、再現可能なコード・source-freeメトリクス・計画はGitHub。

**運用上の必須条件**
- 選択→変換→結果確認→PNG/SVG取得がiPhone PWAとPCの双方で成功。
- 最高品質のZeroBase2とLocal V2 fallbackは明示。fallback品質を「BEST成功」に見せない。
- LocalWorkerはloopbackバインド、Tailscale Serveはtailnet専用、owner-identityとOriginを検証。Funnelなし。Service Workerが画像/APIをキャッシュしない。
- 障害、429競合、起動/復旧、RAM不足、Tailscale断、再接続、差戻しを検証し、無関係プロセスは止めない。

## 現在地（根拠）

- GitHub main at planning time: `0bd291ea14f5822f951ca447c76cd6d5f2a04947`。既存Local/Public分離・routeは `docs/MINIMALIZER_LOCAL_PUBLIC_SPLIT_20261008.md`、Local HTMLは `local_worker/frontend/index.html`、adapterは `local_worker/frontend/local-route.js`、APIは `local_worker/app.py`。
- 実機接続/Origin修正の記録は `docs/handoffs/HND-20261008-MINIMALIZER-LOCAL-ORIGIN-RELOAD-RECOVERY.md`。過去の /health + Origin が200であり、今日の全画像E2E完了を意味しない。
- Private Drive `RUN188_CHECKPOINT_20261015.md` (ID `1ugpaHU0mBPM7mnMqf3_CiLBkOWkeyeOJ`) : Run184–188研究の74 pytest PASS、13 shadow artifacts deterministic 3回、既存H04マスク11/11 SHA一致。**品質・統合HOLD**。原形状は head 1 component, torso 2 components, hair 4 components。V6候補は torso 2維持、hair 6に増加、9,150 hair候補画素の正しい所属が未確定。Phase5 graph PASSは意味的正解の証明ではない。PC production workerのgraph実装とGitHub mainのgraph実装に差分がある。
- `docs/references/KYOKO_MANUAL_REFERENCE_V1_20261015.md`: ユーザー採用済み手描き参照（顔・上半身340×340、33図形）。見本の下敷きSHA ≠ 署名済みGC001なのでピクセル教師として直接適用不可。
- 既存キャンペーン `docs/campaigns/CMP-20261009-SA1060-TO-PRODUCTION.json` は `ACTIVE_RELEASE_HOLD`。この計画の承認や実施はC08の定時タスク再開／Public本番承認ではない。

## 採用・進捗（2026-10-15）

- **ロードマップ採用:** ユーザー承認、PR #397 → main `58be43f6`。
- **L00 COMPLETE（監査）:** 稼働中ProductionWorkerの主要コードとGitHub mainのGit blobを照合し、HTTP配信4ファイルとdiskのSHA-256が4/4一致。旧作業ツリーの未コミット差分は保持。
- **L01 COMPLETE（入力・評価準備）:** H04 Phase4 11/11 private PNGマスク・Stage記録を独立アーカイブで再検証。Approved78全件台帳を確認。署名済み元画像を自動昇格しない台帳/validatorと12件の負例を含む単体テストを追加。
- **実施・統合記録:** [PR #398](https://github.com/watarionn/Minimalizer/pull/398), main `6ae652ce`; [L00/L01 closure](MINIMALIZER_LOCAL_L00_L01_CLOSURE_20261015.md)。
- **未解決・今後の入力ゲート:** 今回H04/GC001/Radenの元画像raw bytesは改めて再ハッシュしていない。L02では署名済み元画像のSHA検査を必須とする。Golden/Stage8/Approved78 full regression/本番/iPhoneはHOLD、定時タスク停止維持。

## 工程・終了条件

| ID | 工程 | 作業内容 | 完了の証拠 |
|---|---|---|---|
| L00 | 正本・実機の差分監査 | GitHub HEAD、PC worker実装/起動設定、依存モデル、Local PWA公開中のHTTP/PWA asset SHA、既存テスト・private Run188を比較。Publicは変更しない。 | 実装・実機差分表、戻し先SHA、実施する修正順序 |
| L01 | Golden素材・手描き参照の検証基盤 | 署名済みH04/GC001/Raden、Approved18/78のソース/マスクをSHA保護。Kyoko Manual Reference v1は**独立した手描き仕様**として活用し、同じ原画像での画素比較は正本同定/登録後にのみ許可。人体部位ROIとレビューフォームを固定。 | 入力Manifest + 負例を含む自動検証 + private審査ボード |
| L02 | Phase4意味分離の修復 | H04のhair/clothes、head/torso、首、左右肩・腕の境界と背景接続を修復。候補9,150pxと衣装らしい領域は独立観測／人間のソース座標注釈で裏付ける。不明ならABSTAIN、髪から服へ一括変更しない。 | 元画像のみからの検証、owner重複なし、保護部位消失なし、head/torso/hair topology・色所有の回帰 |
| L03 | Phase5接続とレイヤー表示順 | Phase4→5を元入力に対して実行し、頭・首・胴体の接続、左右腕、髪と袖の重なり、衣装欠損、細部の孤立成分を検査。GitHub main版を原点にPC側旧実装との差分を明示。 | Graph PASS + 元構造に対するtopology/semantic検査PASS、実際の人物画像で目視確認 |
| L04 | SVG幾何と色の品質 | 正式Stage8**元ソース頂点数**と展開後SVGの数値を別ゲートにする。出力シルエットと腕/服/髪ROI、ColorStrip/characteristicの色所有、アクセサリ、細い構造を検証。顔の大面積スキン下敷きを禁止。 | 署名済み構造ゲート・実Chromium DPR1/DPR2・面積/輪郭/所有者差分・人間比較。既存頂点上限が無理なら**人間承認の版付き方針**で別判定 |
| L05 | エンジン統合・失敗時動作 | 完成したPhase4→8を候補モードで丸ごと実行。品質ゲートで失敗した場合は不明品質を成功にしない。ZeroBase2 BEST／V2 fallbackと理由をUIに表示。画質研究だけでなくPWA全体の入力→出力E2Eを固定。 | ルート/APIの返答、トレースSHA、rollback可能な統合PR、PNG/SVGの一致確認 |
| L06 | Golden・回帰審査 | H04を含む本人が指定した中核Goldenを独立A/B目視、欠損があればFAIL。Approved18→Approved78（歴史的expected SHA authorityを確認）、Chrome両DPR、無人物/多人物/背景/小部品/透明画像などの失敗系、画質だけでなく遅延/メモリも測る。 | 必須Golden全ケース署名済み、人間の重症FAILゼロ、Approved18/78の再現可能な検証報告 |
| L07 | Local PWAとWorkerの運用仕上げ | Tailscale/owner/Origin、cold/warm起動、単一処理lockの429、接続断・キャンセル・メモリ不足、ログ/進捗、Service Workerの画像非キャッシュ、iPhone Safariの保存・再起動・オンライン復帰を検証。 | PCとiPhoneの実操作証跡、権限外拒否、機密非漏洩、復旧手順、実測処理性能 |
| L08 | リリース・最終受入 | バージョン固定、shadow→限られたprivate本番昇格、失敗時即ロールバック、ライブレスポンスの正しいroute/asset SHA確認、iPhoneユーザー受入、PRマージ/Drive保管。 | 実機で完成品質の入力→出力PASS、ユーザー承認、remote SHA一致、rollback実証、正式完成判定 |

## 実行順の重要事項

1. **最初の実装バッチはL00 + L01。** mainとPC production workerの差分が既知のため、誤ったgraph実装を使う検証を停止。手描き見本のGC001対応は内容同一と仮定しない。Golden用の入力Authorityと比較画像を整える。
2. L02とL04（幾何・ColorStripの非破壊研究）、L07（PWA安全性の非破壊テスト準備）は並行可能。L02の意味分離がHOLDでも無関係な安全なテスト整備を止めない。
3. **最重要品質ゲートはL02→L03。** H04の9,150px境界・頭胴体接続・腕の重なりが未解決のままL05を採用しない。独立解析器のconfidence自体は正解ラベルではない。
4. L04のsource Stage8 ring budgetは compressed SVG capで代用しない。人間の政策変更承認なしに制限緩和したことにしない。
5. L06のPASSが揃うまでL08で品質承認しない。ただしL07の認証/再接続/復旧テストは先に実施可能。
6. 公開GitHubはコード・メタデータ・抽象化した計測だけ。非公開原画・source SVG、細かな座標、実機秘密情報は指定Driveに置く。GPU/実機・Tailscale実証が必要になるまでRDCを使わない。

## 完成までに必要な本人確認

- **判定A:** L02の重要な髪/服/腕境界の署名済み原画像に対する専門家または本人のROIラベル確認（モデルで独立検証できない箇所）。
- **判定B:** L04で元Stage8ルールを満たせない場合に限る、歴史FAILを保存する版付き新方針承認。
- **判定C:** L06の本当のGolden目視判定。Kyoko Manual Reference v1の採用はこの承認ではない。
- **判定D:** L08のiPhone完成品を本人が操作し、正式採用/ロールバック方針を承認。

## 検証・完成基準の原則

- 「テスト件数のPASS」「同じSHAで再現」「Graph PASS」「人物として自然」はそれぞれ別証拠。
- 画質の正解は**元画像の特徴維持＋ユーザーが意図するミニマル表現＋本人の本物の目視承認**で判断。数値の閾値は今ある署名済み基準との一致で設定し、新しい目標値を勝手に作らない。
- エラーは最初に原因帰属（入力・前処理・owner・graph・幾何・描画・UI・運用）をして、その工程だけを研究。PASS条件に達しない場合は候補不採用・明示HOLD。
- 定時キャンペーン停止中。計画策定・PR mergeは自動実行再開を意味しない。
- 期間見積はL00の実装差分とL02の意味ラベル確定後に更新する。技術的に未検証の領域について固定の納期や達成率を断言しない。

## 次回最初に実行すること

1. GitHub mainの `local_worker/app.py`、`local_worker/frontend/*`、`minimalizer_zerobase/**` と、実機で現在起動しているWorkerのSHA/起動構成の**読み取り比較**。
2. Drive `RUN188_CHECKPOINT_20261015.md` のH04 signed originals + original Phase4 mask lineageから、`hair/clothes/torso/head`の右衣装・肩境界の現状レビュー画像を再確認。
3. LocalとPublicの検証/出力を別ディレクトリへ保持し、L00監査とL01ソースManifestをsource-free PRにまとめる。

**この文書は採用済みLocal完成計画。L00/L01は監査・評価準備完了であり、Public/C08ステータス、署名済み原物、本番Worker、ユーザーのGolden/リリース承認を変更しない。**
