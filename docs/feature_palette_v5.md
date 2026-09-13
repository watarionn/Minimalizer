# Feature Palette v5

Minimalizerで利用するためのAI非依存・特徴色選抜モジュールです。

配置先:

- `minimalize_engine/palette/feature_palette.py`
- 公開API: `minimalize_engine.palette.extract_feature_palette`
- Color Strip連携: `minimalize_engine/characteristic_color_strip.py`
- 公開API: `minimalize_engine.extract_characteristic_color_strip`

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

## 特徴色だけを取得する

```python
from PIL import Image
from minimalize_engine.palette import extract_feature_palette

image = Image.open("input.png")
palette = extract_feature_palette(image, n_colors=4)

for color in palette:
    print(color.hex, color.family, color.score)
```

## Color Stripとして利用する

既存の `extract_color_strip()` は変更せず、比較検証用の独立ブリッジを追加しています。

```python
from minimalize_engine import (
    extract_characteristic_color_strip,
    color_strip_to_svg,
)

document = extract_characteristic_color_strip(
    "input.png",
    color_count=4,
    order="most_first",
    remove_background=True,
)
svg = color_strip_to_svg(document)
```

特徴色選抜後の各色には、解析画像の全可視画素をLab距離で再割り当てして `pixel_count` / `share` を付与します。そのため既存の `ColorStripDocument`、SVG出力、PNGレンダリング、equal/proportional表示をそのまま再利用できます。

## 現在の統合状態

- 特徴色抽出モジュール: 実装済み
- `ColorStripDocument` への変換ブリッジ: 実装済み
- `minimalize_engine` 公開API: 実装済み
- ブリッジ用ユニットテスト: 追加済み
- 既存 `extract_color_strip()` の既定挙動: 変更なし
- Web UI / `color_strip_path()` からの選択: まだ未接続
- 通常のMinimalizeパイプラインへの特徴色保護: まだ未接続

次の候補は、Web UIのColor Stripに `characteristic` 選択モードを追加して、`dominant / featured / characteristic` を同一画像で比較できるようにすることです。
