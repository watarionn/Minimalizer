from pathlib import Path

from PIL import Image, ImageDraw

from minimalize_engine.palette import extract_feature_palette

from minimalize_engine import (
    color_strip_to_svg,
    extract_characteristic_color_strip,
    render_color_strip,
)


def _fixture_image(path: Path) -> None:
    image = Image.new("RGB", (120, 120), (245, 220, 225))
    draw = ImageDraw.Draw(image)
    draw.rectangle((20, 15, 95, 105), fill=(245, 245, 240))
    draw.rectangle((25, 25, 70, 95), fill=(220, 40, 45))
    draw.rectangle((70, 30, 92, 62), fill=(245, 205, 55))
    draw.rectangle((70, 66, 94, 96), fill=(80, 205, 215))
    image.save(path)


def test_characteristic_color_strip_builds_document(tmp_path: Path) -> None:
    path = tmp_path / "sample.png"
    _fixture_image(path)

    document = extract_characteristic_color_strip(
        path,
        color_count=4,
        order="most_first",
        remove_background=True,
    )

    assert document.color_count == 4
    assert document.source_width == 120
    assert document.source_height == 120
    assert sum(color.pixel_count for color in document.colors) == 120 * 120
    assert all(0.0 < color.share <= 1.0 for color in document.colors)


def test_characteristic_color_strip_uses_existing_renderers(tmp_path: Path) -> None:
    path = tmp_path / "sample.png"
    _fixture_image(path)
    document = extract_characteristic_color_strip(path, color_count=4)

    svg = color_strip_to_svg(document)
    raster = render_color_strip(document)

    assert svg.startswith('<svg xmlns="http://www.w3.org/2000/svg"')
    assert svg.count("<rect") == document.color_count
    assert raster.size == (document.output_width, document.output_height)


def test_role_balancing_keeps_dark_main_and_small_chromatic_accent(tmp_path: Path) -> None:
    path = tmp_path / "role-balance.png"
    image = Image.new("RGB", (160, 120), (24, 24, 28))
    draw = ImageDraw.Draw(image)
    draw.rectangle((12, 12, 147, 107), fill=(34, 35, 40))
    draw.rectangle((25, 24, 72, 96), fill=(235, 231, 226))
    draw.rectangle((118, 26, 143, 58), fill=(35, 180, 188))
    draw.rectangle((116, 68, 142, 98), fill=(195, 48, 55))
    image.save(path)

    with Image.open(path) as source:
        palette = extract_feature_palette(source, n_colors=4, remove_background=False)

    families = {color.family for color in palette}
    assert any(color.neutral_kind == "dark" for color in palette)
    assert families & {"cyan", "blue", "green"}
    assert families & {"red", "pink", "orange"}
