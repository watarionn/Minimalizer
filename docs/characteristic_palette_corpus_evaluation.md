# Characteristic Palette v5 corpus evaluation

`dominant / featured / characteristic` を、既存の実画像 corpus 16枚で横並び比較した結果です。

## 結論

`characteristic` は、単純な使用量順より「キャラクターを識別しやすい色」を拾う傾向が明確に強くなりました。
特に、差し色・白・肌寄りの淡色・青/赤系アクセントの回収が改善しています。

ただし、現時点では **標準色選抜への即時昇格は保留** とします。
理由は、暗色主体・単色主体・風景で、構造を支える暗い主色を落としたり、同系統の淡色を複数枠に残すケースがあるためです。

## 改善が分かりやすいケース

- Ichijou Ririka: 淡色 + 紫 + 赤 + 暗茶の役割分離が良好
- Isaki Riona: 黒/白/青灰/ワインの4役が明確
- Koganei Niko: オレンジ差し色を維持しつつ、無彩色重複を削減
- Mizumiya Su: 水色系のキャラクター性をより強く反映
- Nerissa Ravencroft: 黒/白/青/濃青の象徴色が明確
- Omaru Polka: 赤/白/青/黄がキャラクター印象に近い
- Oozora Subaru: 黄緑/肌色/水色/赤の識別色を回収
- Otonose Kanade: 白/茶/コーラル/赤の役割が整理
- Rindo Chihaya: 黒/淡色/茶/青緑の分離が良好
- Shirogane Noel: 白/黒/茶/金系が装備・髪・衣装の印象に合う

## まだ混在するケース

- Elizabeth Rose Bloodflame: 赤系の整理は良いが、黒の主役感が弱くなる
- Juufuutei Raden thumbnail: 緑と黒は良いが、4枠目の暖色がやや強い
- Juufuutei Raden full: 黒主体の衣装に対し暖色を拾いすぎる
- Kikirara Vivi: 紫/ピンクは良いが、中間の茶灰色が代表色として弱い
- Night River City: 夜景の金色は拾えるが、強い赤のネオンを落とす
- Todoroki Hajime: 紫系に寄りすぎて、濃い構造色が消える

## 次の実装方針

次段階は `Role-based Selection` とし、4枠を単なる上位4色ではなく役割で配分します。

- Main: 面積と構造を支える主色
- Neutral: 白/黒/灰など必要な無彩色
- Accent: 小面積でも識別性の高い差し色
- Support: Main と Accent の間をつなぐ補助色

特に、暗色主体画像では Main/Neutral のどちらかに一定量の暗色を予約し、単色主体では同系統色の重複上限を設けます。
風景画像では、局所的な高彩度アクセントを1枠残す救済を追加します。

## 比較ツール

`tools/compare_color_selection.py` で既存 corpus を一括評価できます。
比較画像とJSONは `artifacts/color-selection-comparison/` に生成します。生成物は評価用のためGit管理対象にはしません。
