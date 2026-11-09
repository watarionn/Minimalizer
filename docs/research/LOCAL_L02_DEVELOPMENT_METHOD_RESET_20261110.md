# L02開発方式の再設計: 画素修正ではなく失敗クラスを解消する

更新日: 2026-11-10

## 決定

H06の4画素除去、H08の591画素回復のような小規模な差分を、候補の更新として
繰り返さない。これは品質改善の開発単位になっていないため、既存のshadow結果と
して保存するだけにする。

今後のAは、次の単位で進める。

```text
失敗クラスを特定
  -> 画像全体を再観測
  -> 意味領域をcomponent単位で再構成
  -> H04/H06/H08を同じ契約で一括凍結
  -> 構造・意味・視覚を一度に評価
  -> 合格なら次段階、失敗なら仮説を破棄
```

## これまでの方法をやめる理由

post-freeze診断では、旧候補の変更量に対して残差が大きすぎる。

| case | 旧候補の変更 | 残っている診断残差 |
|---|---:|---:|
| H06 | 4px除去 | known-negative owner 11,547px、unknown predicted 80,766px |
| H08 | 591px回復 | known-positive未回復 59,444px、unknown predicted 3,814px |
| H04 | 0px変更 | known-negative owner 4,423px |

この状態で4pxや591pxを追加しても、腕・袖・下着・正衣装・遮蔽の意味境界は
解決しない。したがって「差分が出た」ことを成果とみなさず、失敗クラス全体を
解消できたかだけを見る。

## 新しい開発サイクル

### 1. 現状を凍結する

- signed source、source SHA、現在のowner、既存候補のSHAを保存する。
- 旧候補は `historical / superseded / not-formal` として参照専用にする。
- 旧ownerを次の推論の入力にしない。
- Phase4 FAILの候補をPhase5やL04へ渡さない。

### 2. 失敗を画素ではなく意味クラスで分類する

最初に、全身について次を一枚の診断表へまとめる。

- 正衣装が消える領域
- 腕・手・袖の誤owner領域
- 下着・肌・装飾の誤owner領域
- 遮蔽順序が不明な領域
- source alpha外、穴、孤立成分、連結成分の分断
- observer間で一致しない領域

この表を作れない局所修正は実装しない。既知ラベルはこの工程の診断には使えるが、
推論入力や閾値決定には使わない。

### 3. source-only observerを束ねる

各observerは署名済み元画像だけを入力にし、モデル、revision、重みSHA、出力SHAを
固定する。人手mask、owner番号、レビューJSONは入力から排除する。未知画素は陰性に
しない。

observerの一致はowner権限ではない。observerが一致しない成分は、その成分全体を
unknownに退避する。

### 4. component単位で意味ownerを再構成する

数画素を追加・削除する関数は正式候補の経路に置かない。衣装、袖、腕、下着、遮蔽の
候補を画像全体から作り、8連結component、穴、接触関係、排他的owner、source alphaを
同時に再計算する。

意味を決められないcomponentは、既存ownerを部分的に壊さず、component全体をunknown
にする。正衣装の保護と誤owner除去を同じ再構成で扱う。

### 5. 三例を同じ実装で一括凍結する

H06だけに効く閾値、H04へ後合わせした閾値、特定の既知maskに合わせた補正は採用しない。
H04/H06/H08を同じobserver bundle、同じcomponent規則、同じreceipt schemaで処理する。
一例だけ改善して他例が悪化した場合、その仮説は不採用にする。

### 6. レビュー可能な大きさで評価する

候補は通常倍率の全体画像、変更componentの拡大画像、owner別before/after、意味コメント
を一つのfreeze SHAに束縛する。

「変更結果を視覚的に受け入れられる」がNOで、その理由が「変更が小さすぎる」なら、
品質が悪いと解釈せず、正式候補として提出しない。候補を作り直し、失敗クラス全体を
含む変更に戻る。

## 実装しない変更

次のどれかに該当する変更は、作業成果として数えない。

- 既存ownerを数画素だけ削る、戻す、橋渡しする。
- class11一律保護、class32単純OR/AND、既知例への閾値後合わせ。
- H04の結果や人手maskをH06/H08の推論へ移植する。
- observerの不在を陰性として扱う。
- metricsだけを改善し、腕・下着・遮蔽・正衣装の意味を説明できない。
- 通常倍率で差分を確認できない候補をPhase4へ送る。

## 現在の大きな実装単位

1. H06/H08で取得済みのSapiens2、DeepFashion2、SCHP ATR18、SCHP LIP20を、source-only
   observer bundleとしてSHA固定する。
2. observerの出力を衣装・下着・腕・袖・遮蔽のcomponent graphへ変換し、全componentの
   owner候補またはunknownを決める。
3. 同じgraphをH04へ適用し、三例を一括freezeする。
4. freeze後にのみ人手評価を行い、Phase4の正式receiptへまとめる。
5. Phase4が三例とも独立PASSのときだけPhase5 exact replay、L04三点セット、Bへのhandoffへ進む。

この順序を完了するまで、BのL04/L05/L07実装、Service Worker世代、production runtimeは
変更しない。Bの既存QA PASSは保持するが、Aの品質FAILを解消したことにはしない。

## 完了判定

この方式の成果はコミット数や候補数ではなく、次の全てで判定する。

- 三例でsource SHAとobserver SHAが一致する。
- 推論前に人手ラベルを見ていないことがreceiptで再現できる。
- unknownを陰性にしていない。
- 正衣装保持、誤owner除去、腕・袖・下着・遮蔽の意味がcomponent単位で説明できる。
- 排他的owner、4/8連結、穴、遮蔽、source alphaの構造検査が通る。
- 通常倍率と拡大倍率の視覚レビューが同じfreeze SHAに対して行われる。
- Phase4が独立PASSになるまでPhase5、L04、Golden、本番へ進めない。

現状はこの判定を満たしていないため、`L02=HOLD / Phase4=FAIL / Phase5=NO_GO / Golden=HOLD / production=NO_GO` を維持する。
