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


def test_file_adapter_preserves_v2_png_contract(tmp_path):
    from minimalize_engine.v2 import minimalize_file_png

    source_path = tmp_path / "source.png"
    bgr = cv2.cvtColor(_image(), cv2.COLOR_RGB2BGR)
    assert cv2.imwrite(str(source_path), bgr)
    direct = export_png(minimalize_v2(_image(), presets=("minimal",)))
    adapted = minimalize_file_png(source_path)
    assert adapted == direct


def test_layered_png_export_is_byte_deterministic_with_seam_fallback():
    from minimalize_engine.v2.analysis_guidance import AnalysisGuidance
    from minimalize_engine.v2.pipeline import LayeredPersonConfig, PipelineConfig

    image = _image()
    subject = np.zeros(image.shape[:2], dtype=np.float32)
    subject[4:50, 8:52] = 0.95
    guidance = AnalysisGuidance(
        subject_prob=subject,
        subject_confidence=np.ones_like(subject),
        subject_provider="test",
        subject_model="mask",
    )
    result = minimalize_v2(
        image,
        presets=("minimal",),
        config=PipelineConfig(
            analysis_max_side=60,
            layered_person=LayeredPersonConfig(enabled=True),
        ),
        guidance=guidance,
    )

    assert result.person_parts is not None
    assert result.person_part_presets
    first = export_png(result, preset="minimal", include_facets=False)
    second = export_png(result, preset="minimal", include_facets=False)
    assert first == second


def test_png_export_can_preserve_source_alpha():
    from minimalize_engine.v2.analysis_guidance import AnalysisGuidance

    image = _image()
    alpha = np.ones(image.shape[:2], dtype=np.float32)
    alpha[:6, :] = 0.0
    alpha[:, :4] = 0.0
    guidance = AnalysisGuidance(alpha=alpha)
    result = minimalize_v2(
        image,
        presets=("minimal",),
        guidance=guidance,
    )

    exported = export_png(
        result,
        preset="minimal",
        preserve_source_alpha=True,
    )
    decoded = cv2.imdecode(
        np.frombuffer(exported.content, dtype=np.uint8),
        cv2.IMREAD_UNCHANGED,
    )

    assert decoded.ndim == 3 and decoded.shape[2] == 4
    expected_alpha = np.rint(result.bundle.alpha * 255.0).astype(np.uint8)
    assert np.array_equal(decoded[..., 3], expected_alpha)
    assert exported.metadata.preserves_source_alpha is True
