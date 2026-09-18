from __future__ import annotations

import numpy as np
from PIL import Image

from minimalize_engine.v2 import (
    ALPHA_BACKGROUND_SCHEMA_VERSION,
    build_alpha_background_compatibility,
    minimalize_file_png,
    resolve_alpha_background_route,
)


def test_alpha_background_policy_is_explicit_and_conservative():
    report = build_alpha_background_compatibility()
    payload = report.to_dict()
    assert payload["schema_version"] == ALPHA_BACKGROUND_SCHEMA_VERSION
    assert payload["preserves_opaque_white_pixels"] is True
    assert payload["preserves_legacy_alpha_features"] is True
    assert resolve_alpha_background_route(
        background_mode="white", source_has_transparency=False
    ) == "v2"
    assert resolve_alpha_background_route(
        background_mode="white", source_has_transparency=True
    ) == "legacy"


def test_alpha_sensitive_background_modes_stay_on_legacy():
    for mode in ("source", "transparent", "custom"):
        assert resolve_alpha_background_route(
            background_mode=mode,
            source_has_transparency=False,
        ) == "legacy"
    assert resolve_alpha_background_route(
        background_mode="white",
        source_has_transparency=False,
        ignore_source_alpha=True,
    ) == "legacy"


def test_fully_opaque_rgba_matches_rgb_v2_png(tmp_path):
    rgb = np.zeros((24, 32, 3), dtype=np.uint8)
    rgb[:, :16] = (220, 40, 35)
    rgb[:, 16:] = (35, 70, 215)
    rgba = np.dstack((rgb, np.full((24, 32), 255, dtype=np.uint8)))
    rgb_path = tmp_path / "opaque-rgb.png"
    rgba_path = tmp_path / "opaque-rgba.png"
    Image.fromarray(rgb, "RGB").save(rgb_path)
    Image.fromarray(rgba, "RGBA").save(rgba_path)
    first = minimalize_file_png(
        rgb_path, preset="minimal", filename="same.png"
    )
    second = minimalize_file_png(
        rgba_path, preset="minimal", filename="same.png"
    )
    assert first.content == second.content
    assert first.metadata.pixel_sha256 == second.metadata.pixel_sha256
    assert first.metadata.png_sha256 == second.metadata.png_sha256
