# Feature Palette v5

Minimalizerで利用するためのAI非依存・特徴色選抜モジュールです。

配置先:

- `minimalize_engine/palette/feature_palette.py`
- 公開API: `minimalize_engine.palette.extract_feature_palette`

## 目的

単純な「使用ピクセル数の多い順」ではなく、人が見たときに画像を特徴づける3〜6色を抽出します。

主な処理:

1. 画像端に広く接続する背景候補を除外
2. CIE Labで近似色をクラスタリング
3. 面積効果を圧縮し、大面積色だけが独占するのを防止
4. Chromaと空間分布を評価
5. 白・黒・灰・低彩度色を別扱い
6. `red / orange / yellow / yellowgreen / green / cyan / blue / purple / pink / beige / brown / bluegray / mauve / white / gray / black` の色ファミリーで重複を抑制
7. 未採用の色ファミリーや小面積アクセント色を救済

## 利用例

```python
from PIL import Image
from minimalize_engine.palette import extract_feature_palette

image = Image.open("input.png")
palette = extract_feature_palette(image, n_colors=4)

for color in palette:
    print(color.hex, color.family, color.score)
```

## Minimalizerへの統合候補

- `color_strip.py` の代表色候補生成
- ミニマル化時の色数削減前の特徴色保持
- Subject / foreground の配色保護
- 背景色とキャラクター色の分離

現時点ではモジュールを追加した段階で、既存パイプラインの既定挙動は変更していません。既存出力を壊さずに比較検証してから接続できます。
