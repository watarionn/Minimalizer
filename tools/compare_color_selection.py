from pathlib import Path
import sys, json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from minimalize_engine.color_strip import extract_color_strip
from minimalize_engine.characteristic_color_strip import extract_characteristic_color_strip

CORPUS = ROOT / "tests" / "assets" / "corpus"
OUT = ROOT / "artifacts" / "color-selection-comparison"
OUT.mkdir(parents=True, exist_ok=True)
MODES = ("dominant", "featured", "characteristic")


def palette_for(path: Path, mode: str):
    if mode == "characteristic":
        doc = extract_characteristic_color_strip(path, color_count=4, order="most_first")
    else:
        doc = extract_color_strip(path, color_count=4, selection_mode=mode, order="most_first")
    return [tuple(c.rgb) for c in doc.colors]


def draw_palette(draw, x, y, width, height, colors):
    n = max(1, len(colors))
    for i, rgb in enumerate(colors):
        x0 = x + round(width * i / n)
        x1 = x + round(width * (i + 1) / n)
        draw.rectangle((x0, y, x1, y + height), fill=rgb)


def main():
    images = sorted(p for p in CORPUS.iterdir() if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})
    cell_w, img_h, bar_h, label_h = 260, 220, 34, 30
    row_h = img_h + bar_h * 3 + label_h
    sheet = Image.new("RGB", (cell_w * 2, row_h * len(images)), "white")
    draw = ImageDraw.Draw(sheet)
    records = []

    for row, path in enumerate(images):
        src = Image.open(path).convert("RGB")
        src.thumbnail((cell_w, img_h))
        y = row * row_h
        sheet.paste(src, (0, y))
        draw.text((cell_w + 6, y + 4), path.name, fill=(20, 20, 20))
        mode_data = {}
        for mi, mode in enumerate(MODES):
            colors = palette_for(path, mode)
            mode_data[mode] = ["#%02X%02X%02X" % c for c in colors]
            by = y + label_h + mi * bar_h
            draw.text((cell_w + 6, by + 8), mode, fill=(20, 20, 20))
            draw_palette(draw, cell_w + 95, by, cell_w - 100, bar_h - 2, colors)
        records.append({"source": path.name, **mode_data})

    sheet.save(OUT / "comparison.png")
    (OUT / "comparison.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"images={len(images)}")
    print(OUT / "comparison.png")
    print(OUT / "comparison.json")


if __name__ == "__main__":
    main()
