from __future__ import annotations

from io import BytesIO

import pytest
from PIL import Image, ImageDraw

from minimalize_engine.color_strip import (
    color_strip_to_svg,
    extract_color_strip,
    render_color_strip,
)


def _dominant_color_image(path) -> None:
    image = Image.new("RGB", (100, 100), (255, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 50, 99, 79), fill=(0, 255, 0))
    draw.rectangle((0, 80, 99, 94), fill=(0, 0, 255))
    draw.rectangle((0, 95, 99, 99), fill=(255, 255, 0))
    image.save(path, format="PNG")


def test_color_strip_selects_most_used_colors_then_renders_least_used_first(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)

    document = extract_color_strip(path, color_count=3, similarity=6)

    assert document.color_count == 3
    assert document.size_mode == "equal"
    assert document.order == "least_first"
    assert document.orientation == "vertical"
    assert [color.rgb for color in document.colors] == [
        (0, 0, 255),
        (0, 255, 0),
        (255, 0, 0),
    ]
    assert [color.pixel_count for color in document.colors] == [1500, 3000, 5000]
    assert [round(color.share, 2) for color in document.colors] == [0.15, 0.30, 0.50]

    svg = color_strip_to_svg(document)
    assert svg.count("<rect ") == 3
    assert svg.index('fill="#0000ff"') < svg.index('fill="#00ff00"') < svg.index('fill="#ff0000"')
    assert 'height="33" fill="#0000ff"' in svg
    assert 'height="34" fill="#00ff00"' in svg


def test_color_strip_can_reverse_to_most_used_first(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)

    document = extract_color_strip(path, color_count=3, similarity=6, order="most_first")

    assert [color.rgb for color in document.colors] == [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
    ]
    assert [color.pixel_count for color in document.colors] == [5000, 3000, 1500]


def test_color_strip_proportional_size_uses_selected_source_shares(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)
    document = extract_color_strip(
        path,
        color_count=3,
        similarity=6,
        size_mode="proportional",
    )

    rendered = render_color_strip(document)
    svg = color_strip_to_svg(document)

    # Selected source counts are 1500:3000:5000. After normalization across
    # selected colors, the 100px output is allocated as 16px, 32px, 52px.
    assert 'height="16" fill="#0000ff"' in svg
    assert 'height="32" fill="#00ff00"' in svg
    assert 'height="52" fill="#ff0000"' in svg
    assert rendered.getpixel((50, 10)) == (0, 0, 255)
    assert rendered.getpixel((50, 30)) == (0, 255, 0)
    assert rendered.getpixel((50, 80)) == (255, 0, 0)


def test_color_strip_can_render_horizontal_segments(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)
    document = extract_color_strip(
        path,
        color_count=3,
        similarity=6,
        orientation="horizontal",
    )

    rendered = render_color_strip(document)
    svg = color_strip_to_svg(document)

    assert 'x="0" y="0" width="33" height="100" fill="#0000ff"' in svg
    assert 'x="33" y="0" width="34" height="100" fill="#00ff00"' in svg
    assert rendered.getpixel((10, 50)) == (0, 0, 255)
    assert rendered.getpixel((50, 50)) == (0, 255, 0)
    assert rendered.getpixel((90, 50)) == (255, 0, 0)


def test_color_strip_ignores_fully_transparent_pixels(tmp_path):
    path = tmp_path / "transparent.png"
    image = Image.new("RGBA", (20, 10), (0, 255, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 9, 9), fill=(220, 40, 30, 255))
    image.save(path, format="PNG")

    document = extract_color_strip(path, color_count=5, similarity=18)

    assert document.color_count == 1
    assert document.colors[0].rgb == (220, 40, 30)
    assert document.colors[0].share == 1.0


def test_color_strip_png_uses_equal_height_bars(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)
    document = extract_color_strip(path, color_count=3, similarity=6)

    rendered = render_color_strip(document)
    buffer = BytesIO()
    rendered.save(buffer, format="PNG")

    assert rendered.size == (100, 100)
    assert rendered.getpixel((50, 10)) == (0, 0, 255)
    assert rendered.getpixel((50, 50)) == (0, 255, 0)
    assert rendered.getpixel((50, 90)) == (255, 0, 0)
    assert buffer.getvalue().startswith(b"\x89PNG\r\n\x1a\n")


def test_color_strip_rejects_unknown_layout_options(tmp_path):
    path = tmp_path / "dominant.png"
    _dominant_color_image(path)

    with pytest.raises(ValueError, match="size_mode"):
        extract_color_strip(path, size_mode="random")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="order"):
        extract_color_strip(path, order="random")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="orientation"):
        extract_color_strip(path, orientation="random")  # type: ignore[arg-type]


def test_color_strip_caps_analysis_and_output_sizes(tmp_path):
    path = tmp_path / "large.png"
    Image.new("RGB", (800, 200), (10, 20, 30)).save(path, format="PNG")

    document = extract_color_strip(
        path,
        color_count=3,
        similarity=18,
        analysis_max_side=200,
        output_max_side=400,
    )

    assert (document.analysis_width, document.analysis_height) == (200, 50)
    assert (document.output_width, document.output_height) == (400, 100)
