# Minimalizer Local L02 Phase5入力bundle作成契約（2026-11-13）

## 目的

現行candidateをPhase5へ進めるための`phase_04`成果を、誰が作成し、誰が評価するかを分離する。独立評価者が推論成果を作ったり、既存Stage8を再利用したりしない。

## 役割

### A開発側（作成者）

A開発側が、固定した署名済み元画像と凍結済みcandidateを使って、H04/H06/H08のcandidate-bound Phase4 bundleを生成する。作成者はCodexでも凛夏でもよいが、同じ入力SHA・同じsource-free手順・同じ出力マニフェストで再現できなければならない。

作成時の禁止事項:

- 人手ラベル、レビューJSON、評価マスクを推論入力に使わない。
- unknown画素を陰性として扱わない。
- 旧Stage8、旧candidate、source-only診断を現行candidateの代用品にしない。
- `major_clothing`への単純なOR/AND、全身置換、数画素の後合わせをcandidate統合と呼ばない。

### 独立評価者（後評価者）

独立評価者は、bundleが凍結された後にのみ、元画像・出力・意味を評価する。candidate owner mapや11部位マスクを修正してはならない。評価者のレビュー結果はPhase4 receiptに反映するが、bundleの作成物にはならない。

## 作成手順

1. H04/H06/H08の署名済み元画像SHAをsource manifestで固定する。
2. 現行candidate NPZのSHA、shape、owner値、生成条件をfreeze receiptと照合する。
3. 元画像だけからsource-onlyの構造・部位推論を実行する。
4. candidate ownerを11部位へ統合する明示的なowner integration処理を実行する。腕、下着、袖、遮蔽、unknown、4/8連結、穴、排他的ownerを検査し、条件を満たさない場合はbundleを生成せずHOLDにする。
5. 次のファイルをH04/H06/H08ごとに生成する。

```text
<root>/<case>/phase_04/stage.json
<root>/<case>/phase_04/metrics.json
<root>/<case>/phase_04/part_masks/head.png
<root>/<case>/phase_04/part_masks/hair.png
<root>/<case>/phase_04/part_masks/face.png
<root>/<case>/phase_04/part_masks/neck.png
<root>/<case>/phase_04/part_masks/torso.png
<root>/<case>/phase_04/part_masks/left_arm.png
<root>/<case>/phase_04/part_masks/right_arm.png
<root>/<case>/phase_04/part_masks/lower_body.png
<root>/<case>/phase_04/part_masks/major_clothing.png
<root>/<case>/phase_04/part_masks/accessory_or_held_object.png
<root>/<case>/phase_04/part_masks/unknown.png
```

6. `stage.json`に、source SHA・source寸法・candidate SHA・`outputs`内の各mask/metrics SHAを記録する。
7. `tools/research/audit_local_l02_phase5_input.py`で、全三例を一括監査する。ファイルの存在だけでなく、PNG signature、寸法、実SHA、metrics SHA、candidate/source bindingを検証する。
8. 監査が`READY`になった場合だけ、同じbundleをPhase5へ渡す。

## 現在の状態

2026-11-13時点では、現行NPZは`candidate_owner`だけを含むcandidate成果であり、11部位のcandidate-bound Phase4 bundleではない。既存のsource-only Phase4/5成果は診断用で、candidate SHAがstageへ結び付いていない。したがって現行のPhase5入力監査は`HOLD / NO_GO`である。

必要なのは評価者への再質問ではなく、candidate ownerを11部位の排他的Phase4成果へ統合するA開発側の実装と、その後の独立評価である。この統合処理が未実装の間は、旧成果のSHAを書き換えてREADYにしてはならない。

## 保存境界

source画像、NPZ、mask、座標、比較画像、bundle本体は非公開Driveへ保存する。GitHubにはこの契約、source-freeコード、テスト、SHA・件数・判定だけを保存する。

判定は次の順を維持する。

```text
A開発側が生成 → 入力監査 → Phase5構造検証 → 独立評価 → receipt → L04三点照合
```

Phase4が独立してPASSするまで、Phase5の正式昇格、L04三点セット、Golden、本番、mergeは行わない。
