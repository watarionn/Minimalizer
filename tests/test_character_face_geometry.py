from pathlib import Path

import cv2
import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize
from minimalize_engine.character.face_geometry import evaluate_face_geometry
from minimalize_engine.character.models import CharacterPartCandidate, CharacterStructure
from minimalize_engine.character.part_types import CharacterPartType
from minimalize_engine.models import Scene, Shape


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _ellipse_mask(
    width: int,
    height: int,
    center: tuple[int, int],
    axes: tuple[int, int],
) -> np.ndarray:
    mask = np.zeros((height, width), dtype=np.uint8)
    cv2.ellipse(mask, center, axes, 0, 0, 360, 255, thickness=-1)
    return mask


def _part(
    pid: int,
    part_type: CharacterPartType,
    mask: np.ndarray,
) -> CharacterPartCandidate:
    ys, xs = np.nonzero(mask > 0)
    x0, x1 = int(xs.min()), int(xs.max())
    y0, y1 = int(ys.min()), int(ys.max())
    return CharacterPartCandidate(
        id=pid,
        part_type=part_type,
        mask=mask,
        bbox=(x0, y0, x1 - x0 + 1, y1 - y0 + 1),
        centroid=(float(xs.mean()), float(ys.mean())),
        area=int(np.count_nonzero(mask)),
        area_ratio=float(np.count_nonzero(mask) / mask.size),
        confidence=0.9,
        side="center",
    )


def _geometry_fixture(*, oversized: bool = False) -> tuple[Scene, CharacterStructure]:
    width = height = 200
    head_mask = _ellipse_mask(width, height, (100, 82), (44, 54))
    face_mask = _ellipse_mask(width, height, (100, 91), (24, 30))
    head = _part(0, CharacterPartType.HEAD, head_mask)
    face = _part(1, CharacterPartType.FACE, face_mask)

    structure = CharacterStructure(
        subject_bbox=(44, 24, 112, 166),
        subject_mask=head_mask,
        parts=[head, face],
        preset="portrait",
        confidence=0.9,
        metadata={
            "face_validation": {
                "accepted": True,
                "confidence": 0.92,
            },
        },
    )

    if oversized:
        face_rx, face_ry = 42.0, 47.0
        eye_left, eye_right = 76.0, 124.0
        mouth_y = 116.0
    else:
        face_rx, face_ry = 24.0, 30.0
        eye_left, eye_right = 91.0, 109.0
        mouth_y = 102.0

    shapes = [
        Shape(
            id=1,
            shape_type="ellipse",
            fill_color=(230, 190, 170),
            cx=100.0,
            cy=91.0,
            rx=face_rx,
            ry=face_ry,
            source_role="character_face_base",
            layer_name="character_face_base",
            semantic_type="character_face",
            character_part="face",
            part_confidence=0.9,
        ),
        Shape(
            id=2,
            shape_type="ellipse",
            fill_color=(30, 30, 35),
            cx=eye_left,
            cy=86.0,
            rx=2.0,
            ry=2.0,
            source_role="character_eye",
            layer_name="character_face_detail",
            semantic_type="character_eye",
            character_part="face",
            part_confidence=0.9,
        ),
        Shape(
            id=3,
            shape_type="ellipse",
            fill_color=(30, 30, 35),
            cx=eye_right,
            cy=86.0,
            rx=2.0,
            ry=2.0,
            source_role="character_eye",
            layer_name="character_face_detail",
            semantic_type="character_eye",
            character_part="face",
            part_confidence=0.9,
        ),
        Shape(
            id=4,
            shape_type="line",
            fill_color=None,
            stroke_color=(60, 35, 40),
            stroke_width=1.0,
            points=[(96.0, mouth_y), (104.0, mouth_y)],
            source_role="character_mouth",
            layer_name="character_face_detail",
            semantic_type="character_mouth",
            character_part="face",
            part_confidence=0.9,
        ),
    ]

    scene = Scene(
        width=width,
        height=height,
        background=(255, 255, 255),
        shapes=shapes,
        metadata={
            "character": {
                "layout": {"enabled": False},
                "details": {
                    "face": {
                        "layout": {
                            "face_bbox": list(face.bbox),
                            "left_eye": [91.0, 86.0, 0.9],
                            "right_eye": [109.0, 86.0, 0.9],
                            "mouth": [100.0, 102.0, 0.9],
                        }
                    }
                },
            }
        },
    )
    return scene, structure


def test_face_geometry_scores_matching_face_high():
    scene, structure = _geometry_fixture(oversized=False)
    metrics = evaluate_face_geometry(
        scene,
        structure,
        min_score=0.72,
        canvas_padding=0.0,
    )

    assert metrics is not None
    assert metrics.score >= 0.82
    assert metrics.passed is True
    assert metrics.retry_reasons == []
    assert metrics.area_ratio_score >= 0.85
    assert metrics.center_score >= 0.95
    assert metrics.eye_span_score is not None
    assert metrics.eye_span_score >= 0.90


def test_face_geometry_rejects_oversized_generated_face():
    scene, structure = _geometry_fixture(oversized=True)
    metrics = evaluate_face_geometry(
        scene,
        structure,
        min_score=0.72,
        canvas_padding=0.0,
    )

    assert metrics is not None
    assert metrics.score < 0.72
    assert metrics.passed is False
    assert "face_geometry_low" in metrics.retry_reasons
    assert metrics.area_ratio_score < 0.30
    assert metrics.eye_span_score is not None
    assert metrics.eye_span_score < 0.75


def test_pipeline_exposes_face_geometry_quality():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
    )
    scene = minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)
    cq = scene.metadata["character_quality"]

    assert scene.metadata["engine_version"] == "0.3.0"
    assert cq["face_geometry_applicable"] is True
    assert 0.0 <= cq["face_geometry_score"] <= 1.0
    assert "face_geometry" in cq["diagnostics"]
    assert cq["diagnostics"]["face_geometry"]["source_face_area"] > 0
    assert cq["diagnostics"]["face_geometry"]["generated_face_area"] > 0


def test_rejected_face_skips_face_geometry_quality():
    false_face = ROOT / "tests" / "assets" / "false_face_phase85.png"
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
    )
    scene = minimalize(false_face, cfg)
    cq = scene.metadata["character_quality"]

    assert cq["face_geometry_applicable"] is False
    assert cq["face_geometry_score"] is None
    assert "face_geometry_low" not in cq["retry_reasons"]


def test_face_geometry_quality_can_be_disabled():
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_character_auto_retry=False,
        enable_face_primitives=True,
        enable_face_geometry_quality=False,
    )
    scene = minimalize(CORPUS / "Isaki-Riona_pr-img_01_a.png", cfg)
    cq = scene.metadata["character_quality"]

    assert cq["face_geometry_applicable"] is False
    assert cq["face_geometry_score"] is None
    assert cq["diagnostics"]["face_geometry"]["disabled_by_config"] is True
