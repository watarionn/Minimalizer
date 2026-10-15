# MinimalizerLocal L00・L01 構造監査とGolden入力基盤

**監査日:** 2026-10-15 JST  
**範囲:** L00 version/runtime inventory + L01 Golden **input registry & fail-closed tooling**. **Neither full Golden, L02 correction, nor product release has passed.**  
**採用したロードマップ:** PR #397 (merged at `58be43f6f0bab0215b4c0bcc6218d1c090a4bf47`).  
**監査時GitHub main:** `58be43f6f0bab0215b4c0bcc6218d1c090a4bf47`.

## L00: 実際に稼働している版を特定

机上の「HEADが最新だから稼働版も同じ」という推測はしない。PC `YWSHTMR` で **読み取りだけ**を行った。

| 対象 | 実測結果 | 運用上の扱い |
| --- | --- | --- |
| GitHub main | `58be43f6` | source / review 正本 |
| PC 別作業ツリー Minimalizer | `2883e7ef` / `web/static/app.js` が追跡済み差分あり | 作業中データ。**上書き・reset・自動同期しない** |
| PC MinimalizerProductionWorker | `f39d2ff5` / tracked clean | 実際に稼働するLocal Workerのコードディレクトリ。HEADはmainと別物 |
| PC Minimalizer_phase15_pr | `9db1a437` / tracked clean | 旧研究ツリー。Local本番と混同禁止 |
| 実プロセス | loopback `127.0.0.1:28764` listen; Python 3.11.9 | Supervisorの既存起動スクリプトはProductionWorkerルートを用いる。プロセスは再起動・変更しなかった |
| Worker `/health` | HTTP 200 `status=ready` `ready=true`, best/active=`zerobase2` | **接続準備の証明**。リアル画像品質のPASSではない |
| Web 4 assets | `/`, `/local-static/local-route.js`, `/static/app.js`, `/sw.js` のHTTP body SHA256 = ProductionWorkerディスクSHA256 **4/4** | 実際の配信バイトまで証明。iPhoneの既存キャッシュまで同定したわけではない |
| Tailnet/owner設定 | Tailscale running、プライベートOrigin設定/owner-loginファイル存在、Serve設定あり | 内容・秘密値は読まない。端末ごとの認証、iPhone E2EはL07 |

**Git blob/content check (ProductionWorker vs GitHub main)**

- `minimalizer_zerobase/structure/graph.py`: **`60848322332ac88297ef2688d06e32f17ed2b8bc`** MATCH.
- `minimalizer_zerobase/production/cross_part_region_graph.py`: **`d87ef8c6b3cdc6946811cf0843cdd764a2ce814c`** MATCH; `graph_macro_renderer.py` imports this module. Separate from `structure/graph.py`.
- `local_worker/app.py`: `67a69ad317a91e782ce60f6bef121f986d9d88a6` MATCH.
- `local_worker/frontend/local-route.js`: `88ff8eac22ba6f6bb54851fa7499fced1522df0c` MATCH.
- `local_worker/frontend/index.html`: `83be60d82db90035b49e9c402a8ad9f45f9fdbc7` MATCH.
- `local_worker/frontend/sw.js`: `9dcf1b658e7c4160a4ce7d9efd0e91242559cbe2` MATCH.
- `web/static/app.js`: `1e5df1c50fd479d7135436f24d49bf6b5de60bcc` MATCH.

**解釈:** ProductionWorker の **全コミットが** GitHub main と同じとは言っていない。上記の実際に照合したファイルだけの同一性である。別作業ツリーのPhase5 `structure/graph.py` は`584ded20...`でmainと異なる。作業ツリーと稼働ディレクトリを混同した評価は破棄する。過去のRun188が「PC graph differs」と呼んだ対象が**どのモジュール/ツリーだったか**は移行時に再評価する。

**Workerランタイム依存ライブラリ (インストール済みvenvのパッケージ情報):** FastAPI 0.141.1, Uvicorn 0.52.4, NumPy 2.4.6, OpenCV 4.14.0.94, ONNX Runtime 1.26.0, rembg 2.0.84, rtmlib 0.0.16, Pillow 12.3.0; Torch not listed. これは**ロードされているモデル重みのハッシュ認証ではない**。rembg/rtmlibの実重みSHA、device selection、画像処理のライブE2EはL02/L07側で確認する。

**元に戻す基準:** 現在の稼働ツリー HEAD は `f39d2ff5`、配信ファイルSHAとLocal起動スクリプトが照合済み。これは**rollback anchorの記録**であり、実際のロールバック操作を試した証拠ではない。Local Worker / Tailscale / Publicの設定は変えていない。

## L01: Golden入力セットの同一性確認

**機械処理をしてよい下準備を完了。** 正式レビュー/採用済み出力のQAとは別。

| Case | authority expected original SHA256 | この実行で新たに確認できたこと | 残すべきHOLD |
| --- | --- | --- | --- |
| H04 | `7d5a62251326e7b2c6ab058fb6bc76af12a8c0b442444344044a79a97ebae0d3` | Run122とRun107をDriveから新規再取得。Phase4 JSONのSHA `def1eac131b60ae12fa14675441f21a342cfdfde7d1b96c168ba351c74a9eec0`一致。**11/11部位PNG byte-identical**。旧Phase5診断2ファイル一致。 | H04署名済み元画像そのものは2 ZIPに含まれないため**この実行で raw source 再ハッシュしていない**。モデル/人間の意味ラベル承認ゼロ、研究品質HOLD |
| GC001 | `75ef1506709f65c39ea6b3501747c74423c7f2822a36d6f2fb7808c4b3f95f9e` | SA1059/C04の署名済み参照経路とGoldenレビュー資料を突合、過去の人間FAIL（subject anatomical right arm at **viewer-left**）を受け入れゲート化 | original raw sourceを今回再ハッシュしていない。真正C04 A/B署名PASSなし |
| Raden | `d9982c74a2d9a0a8cd3547f3f5cc603a809e942e6dcf62b98e36bfa019903a00` | SA1059/C04の署名済み参照経路とGoldenレビュー資料を突合 | original raw sourceを今回再ハッシュしていない。真正C04 A/B署名PASSなし |
| Kyoko Manual Reference v1 | 手作業の下敷き `cb747da9cf8cecdf052608f4fd1093c647d5250486f72fed39368e96e9e533a2` | 登録済み原本ZIPを再ダウンロード。SHA `63fd3a8b9b730ad641916b5daf14c8d149c508ac5a29aec2e2ac5c502e129db4`一致 | 署名済みGC001元原画とはSHA不一致。ピクセル単位の真値ではなく**独立した形状・色・重ね合わせ見本** |
| Approved18 / 78 | `docs/zerobase/approved78_manifest.json` Git blob `86f413c77760756081273049a3bb02602dc5b2c1` | 78件全件が1–78の連番・重複なし。first 18をApproved18として固定、Drive Approved78 canonical README (2026-09-18) に記載された原則も確認 | 78個のPNG original/reference一枚ずつの画像SHA/レンダー品質は**今回未検証**。データセットのPASSを装わない |

既存 **C04 Golden Review Kit** と SA1059 Review board は審査テンプレートと**旧候補の比較素材**であり、現在のLocalの採用候補や実機の出力そのものではない。Run188研究は74/74 tests・13ファイルの決定性があっても本番・部位意味品質はHOLD。

**実装したゲート**

- `docs/references/MINIMALIZER_LOCAL_GOLDEN_INPUT_REGISTRY_V1.json`: coordinate-free case/version/authority/審査基準台帳。元画像・部位マスク・座標を収録しない。
- `tools/qa/verify_local_reference_registry.py`: 署名済み入力の同一性を偽らず、Approved78原本manifestのGit blob SHAと78連番/重複、H04両アーカイブのSHA + Phase4 11 maskのbyte-exact一致を**失敗時に止める**。
- `tests/test_local_reference_registry.py`: オリジナル写真・実マスクを一切含まない12件の正常/異常テスト **12 PASS**。個別の元画像が手元にないままPASSとなるような入力昇格は禁止。
- Private Driveの保管資料: `MinimalizerLocal_L00_L01_Private_Audit_20261015.zip`。11 mask個別SHA・実検証レシート・未署名Reviewer A/B CSV（各36行 = 3ケース×DPR1/2×6項目）を保管。ユーザーの元画像や座標は公開GitHubへ出さない。

**L01で確立した基準は「人が見るべき画像とその来歴を固定したこと」。本物の人間によるGolden合格、Approved-78全面再実行ではない。**

## 使い方・再開

```sh
python -m unittest discover -s tests -p 'test_local_reference_registry.py' -v
python tools/qa/verify_local_reference_registry.py \
  --registry docs/references/MINIMALIZER_LOCAL_GOLDEN_INPUT_REGISTRY_V1.json \
  --approved78 docs/zerobase/approved78_manifest.json
# Approved-78 and original-source artifacts are private; paths are examples:
python tools/qa/verify_local_reference_registry.py \
  --registry docs/references/MINIMALIZER_LOCAL_GOLDEN_INPUT_REGISTRY_V1.json \
  --run122-private /private/Minimalizer_Run122_H04_Immutable_Phase4_Masks_Private_20261015.zip \
  --run107-private /private/Minimalizer_Run107_H04_Phase3To5_Evidence_Private_20261014.zip
```

L00/L01は**監査・評価前処理として完了**。L02に入る際は、署名済み元画像をraw bytesで再取得・SHA一致してから意味分離テストへ進む。PC作業ツリーの無承認同期・旧Phase5 module読替え禁止。L03の統合前にも同一バージョン証明を再測定する。

**残る人間承認:** H04/GC001/Radenのソース対応の意味ラベルが必要な場所、正式Golden A/B、Stage8方針改定が必要な場合の承認、最終iPhone受入。**定時キャンペーンは停止したまま。**
