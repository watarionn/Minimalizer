# L02 六能力checkpoint availability audit（2026-11-10）

この文書は、ルートI（既存checkpoint採用）を継続できるかの差分監査である。
原画像、マスク、NPZ、座標、比較画像は保存しない。モデル名や論文の能力を、実行可能な
checkpointの存在と混同しない。

## 採用条件

採用候補は、同一revision・重みSHA・推論契約でH04/H06/H08へsource-only実行でき、次の
六能力を一つのbundleとして出力できなければならない。

`outerwear / underlayer / sleeve / arm / pairwise occlusion / instance grouping`

単一semantic mask、人物全体instance、depthからの推測、`topwear`の改名は不採用とする。

## 新規に確認した公開候補

### Spectrum

- 公開プロジェクト: https://s-pectrum.github.io/
- 公開説明上は衣服・身体部位のpart parsingとinstance groupingを扱う。
- しかしプロジェクトページの公開導線は論文、補足資料、ポスターであり、Minimalizerで
  実行できる推論コード・重みrevision・checkpoint SHAは確認できなかった。
- よって、現時点では「能力説明は有望だが、実行可能checkpointなし」=`ROUTE_I_HOLD`。
  論文の主張だけで三例probeやPhase4へ進めない。

### FASHN Human Parser

- 公開モデル: https://huggingface.co/fashn-ai/fashn-human-parser
- arms/handsとtop/dress/skirt/pants等の18 semantic classを出力する。
- garment instance ID、pairwise occlusion、人物内instance groupingの契約がないため、
  六能力observerとしては不採用。既存のローカルprobe結果もこの判定と一致する。

### Sapiens2 body-part segmentation

- 公開モデル: https://huggingface.co/facebook/sapiens2-seg-1b
- body-part semantic segmentationであり、外衣・下層のgarment instance、pairwise遮蔽、
  人物内garment/body groupingを同時に出力するcheckpointではない。
- 既存のH04/H06/H08 source-only probeは能力不足を確認済みで、再実行しない。

### 衣服instance segmentation

- ローカルにある衣服Mask R-CNN系はgarment instanceを出力するが、腕の肌領域、下着層、
  pairwise遮蔽関係がない。六能力を満たす合成observerへ自動昇格させない。

## 判定

```text
route I: executable six-capability checkpoint  NOT_AVAILABLE
route II: Minimalizer-specific observer learning  REQUIRED
L02 / Phase4                         HOLD / FAIL
Phase5 / Stage8 / Golden / production NO_GO
```

## ルートIIの次工程

1. H04/H06/H08を学習へ混ぜず、未見holdoutとして凍結する。
2. 別のアニメ人物・衣装・ポーズ・遮蔽から、人物instance、外衣、下層、袖、腕、接触境界、
   3 pairの遮蔽、unknown/not-visible/not-applicableを別annotationで用意する。
3. source-freeの学習split・loss・再現コマンド・出力SHA receiptを先に固定する。
4. 学習済みobserverをN0-N6へ通し、三例一括でのみcandidateを生成する。

学習データまたは所有者操作が取得できるまで、既存候補の数画素修正、閾値変更、Phase4
receipt追加、Bへの品質handoffは行わない。
