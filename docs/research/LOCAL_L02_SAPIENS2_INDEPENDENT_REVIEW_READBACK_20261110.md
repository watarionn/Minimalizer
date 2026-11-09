# Sapiens2独立visual review readback

更新日: 2026-11-10

## 受領した人間回答

- Drive file: `H04_H06_H08_Sapiens2_独立visual_review_signed_20261110.txt`
- Drive ID: `1DrpR2bYIdDi-KPcyTqkzAm39g30qN3Ni`
- downloaded size: `1122` bytes
- downloaded SHA-256: `8e83eabc93f1e6beb559beb713d79a49ac9bb280ec5ab772397d7af969f4950c`
- reviewer ID: `Tento`
- reviewed at: `2026-11-10 07:47 JST`
- response signature field: `てんと`

回答の意味は、H04では全項目が肯定、H06/H08では「変更結果が悪い」ではなく、
通常倍率で差分が小さすぎて人間には変更箇所を判定できない、というものだった。
元の質問文がこの二つを一つのyes/noに混ぜていたため、機械的に品質FAILへ変換しない。

## 候補差分の事実

freeze receiptに束縛された候補との差分は次の通り。

| case | candidate SHA | 変更画素 | bbox (x1,y1,x2,y2) | 解釈 |
|---|---|---:|---|---|
| H04 | `5b56899313d57b1677cb6c30676fe2e60c9fa141331a379aff7ee7a0e6101b5e` | 0 | - | 変更なし |
| H06 | `87278640b0761e6d3aa572cb37156f13ee09bc8c9ebaef133445ffec63bbfa76` | 4 | `(1237,1090,1307,1150)` | 通常倍率では判定困難 |
| H08 | `8daafac9aabac48635d73b393a8220dd64f88b3a2ef6d7c06ae76b52b049f091` | 591 | `(799,639,1163,724)` | 通常倍率では判定困難 |

## ゲートの扱い

- H04: 受領回答上の意味評価は肯定。ただし候補変更がないため、品質改善の証拠とは別扱い。
- H06/H08: `change_visibility_sufficient=false` 相当。これは品質FAILではない。
- H06/H08の `visual_regression_acceptable` は、元回答だけでは明示されていないため未確定。
- よって現時点は `Phase4=HOLD`、`Phase5=NO_GO`。この判断は「画像が悪い」ではなく、
  レビュー項目の分離と候補差分の視認確認が未完了という意味である。

## 次の具体的作業

1. H06/H08の変更領域を拡大表示したprivate review boardを作る。
2. 評価者には次の二問だけを再回答してもらう。
   - 「候補は、元候補に対して視覚的な悪化を起こしていないか」
   - 「意図した腕・衣装修復を判定できるだけの差分が見えるか」
3. 回答を、既存の一つのyes/noではなく、
   `visual_regression_acceptable` と `change_visibility_sufficient` に分けてreceipt化する。
4. H06/H08の視認可能な改善が確認できない場合は、source-only候補の改善へ戻り、
   Phase4を昇格しない。

このreadbackはsource-freeであり、原画像・マスク・NPZはGitHubへ保存しない。
