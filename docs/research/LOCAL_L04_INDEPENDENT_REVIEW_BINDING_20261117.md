# L04 独立評価readback結合 — 2026-11-17

採用候補receipt `381b0b5a…` の内部summaryは、実装ミスにより
`L04_formal=HOLD / Golden=HOLD`を保持している。一方、同じ候補SHAに対する既存の
独立評価readbackは、三例の三点配信監査と意味評価を完了し、4項目すべて「はい」、
`review_gate=PASS`、`L04_formal=PASS`、`Golden=PASS`を返している。

`tools/research/local_l04_independent_review_binding.py` は、評価者へ再依頼せず、
既存readbackを次の条件でsource-free検査する。

- 候補receipt SHAが現行候補と一致
- H04/H06/H08の元画像・Stage8 JSON・展開SVGのSHAが3例すべて存在
- reviewerが独立と明示されている
- 数値監査・B配信監査・4項目の意味回答がPASS/はい
- 本番は `NO_GO`、release authorizationは `false` のまま

このadapterが返す `L04_formal=PASS` と `Golden=PASS` は、独立評価の品質判定だけを
表す。production許可、Phase5昇格、Aの意味品質、iPhone受入を代行しない。

検証:

```text
python -m pytest -q tests/test_local_l04_independent_review_binding.py
```

private画像・マスク・SVG本体は保存せず、評価者の既存readbackとSHAだけを参照する。
