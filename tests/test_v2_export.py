from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import cv2
import numpy as np

from minimalize_engine.v2 import export_png, minimalize_v2, render_scene
from minimalize_engine.v2.facet import PlanarFacetOverlay
from minimalize_engine.v2.regression import algorithm_digest


def _image() -> np.ndarray:
    image = np.zeros((52, 60, 3), dtype=np.uint8)
    image[:, :30] = (220, 70, 95)
    image[:, 30:] = (55, 100, 210)
    image[10:42, 20:40] = (245, 215, 75)
    return image


def test_png_export_is_byte_deterministic_and_matches_renderer():
    result = minimalize_v2(_image(), presets=("minimal",))
    first = export_png(result)
    second = export_png(result)
    assert first == second
    assert first.content.startswith(b"\x89PNG\r\n\x1a\n")
    decoded_bgr = cv2.imdecode(
        np.frombuffer(first.content, dtype=np.uint8), cv2.IMREAD_COLOR
    )
    decoded = cv2.cvtColor(decoded_bgr, cv2.COLOR_BGR2RGB)
    expected = render_scene(result.presets["minimal"].scene)
    assert np.array_equal(decoded, expected)
    assert first.metadata.pixel_sha256 == hashlib.sha256(expected.tobytes()).hexdigest()
    assert first.metadata.png_sha256 == hashlib.sha256(first.content).hexdigest()
    json.dumps(first.metadata.to_dict(), sort_keys=True)


def test_png_export_metadata_and_baseline_opt_out_are_explicit():
    result = minimalize_v2(_image(), presets=("minimal",))
    normal = export_png(result)
    baseline = export_png(result, include_facets=False)
    scene = result.presets["minimal"].scene
    assert normal.metadata.contract_version == "minimalizer-v2-png-v1"
    assert normal.metadata.preset == "minimal"
    assert normal.metadata.scene_facet_count == len(scene.facet_overlays)
    assert normal.metadata.rendered_facet_count == len(scene.facet_overlays)
    assert baseline.metadata.scene_facet_count == len(scene.facet_overlays)
    assert baseline.metadata.rendered_facet_count == 0
    assert baseline.metadata.include_facets is False


def test_png_export_rejects_missing_preset():
    result = minimalize_v2(_image(), presets=("minimal",))
    try:
        export_png(result, preset="balanced")
    except ValueError as exc:
        assert "preset is not present" in str(exc)
        return
    raise AssertionError("missing preset was accepted")


def test_algorithm_digest_tracks_scene_facet_overlays():
    result = minimalize_v2(_image(), presets=("minimal",))
    pipeline = result.presets["minimal"]
    region_id = pipeline.scene.shapes[0].region_id
    overlay = PlanarFacetOverlay(
        region_id=region_id,
        rgb=(17, 23, 31),
        line_a=1.0,
        line_b=0.0,
        line_c=0.0,
        variant_side=1,
    )
    modified_scene = replace(pipeline.scene, facet_overlays=(overlay,))
    modified_pipeline = replace(pipeline, scene=modified_scene)
    modified = replace(result, presets={"minimal": modified_pipeline})
    assert algorithm_digest(result, "minimal") != algorithm_digest(modified, "minimal")
