from __future__ import annotations

import sys
from io import BytesIO

from PIL import Image, ImageDraw

from app import cli
from minimalize_engine.v2 import minimalize_file_png


def _sample_png() -> bytes:
    image = Image.new("RGB", (64, 48), (242, 238, 228))
    draw = ImageDraw.Draw(image)
    draw.rectangle((8, 8, 32, 40), fill=(45, 75, 120))
    draw.ellipse((36, 12, 56, 32), fill=(210, 100, 80))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_cli_v2_shadow_is_opt_in_and_preserves_contract(tmp_path, monkeypatch, capsys):
    source = tmp_path / "source.png"
    legacy_svg = tmp_path / "legacy.svg"
    v2_png = tmp_path / "shadow-v2.png"
    source.write_bytes(_sample_png())

    parsed = cli.build_parser().parse_args([str(source)])
    assert parsed.v2_shadow_png is None

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "minimalizer",
            str(source),
            "-o",
            str(legacy_svg),
            "--level",
            "5",
            "--v2-shadow-png",
            str(v2_png),
        ],
    )
    cli.main()

    expected = minimalize_file_png(source)
    assert legacy_svg.read_bytes().startswith(b"<svg")
    assert v2_png.read_bytes() == expected.content
    output = capsys.readouterr().out
    assert "V2 contract: minimalizer-v2-png-v1" in output
    assert expected.metadata.png_sha256 in output
