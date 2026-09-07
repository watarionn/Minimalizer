from pathlib import Path

import cv2
import numpy as np

from minimalize_engine import MinimalizeConfig, minimalize


ROOT = Path(__file__).parents[1]
CORPUS = ROOT / "tests" / "assets" / "corpus"


def _scene_for(name: str, **overrides):
    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=240,
        target_max_shapes=32,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
        **overrides,
    )
    return minimalize(CORPUS / name, cfg)


def _write_rgba(path: Path, rgba: np.ndarray) -> None:
    bgra = cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA)
    ok, buf = cv2.imencode(path.suffix or ".png", bgra)
    assert ok
    path.write_bytes(buf.tobytes())


def _make_false_face_image() -> np.ndarray:
    rgba = np.zeros((220, 170, 4), dtype=np.uint8)

    # Torso and body silhouette.
    cv2.rectangle(rgba, (58, 84), (112, 186), (80, 120, 170, 255), -1)
    cv2.rectangle(rgba, (48, 184), (72, 214), (70, 90, 140, 255), -1)
    cv2.rectangle(rgba, (98, 184), (122, 214), (70, 90, 140, 255), -1)

    # Head silhouette without a real face.
    cv2.circle(rgba, (85, 54), 34, (105, 80, 150, 255), -1)
    # Hat / ornament that used to look face-ish.
    cv2.ellipse(rgba, (85, 48), (26, 10), 0, 180, 360, (245, 235, 150, 255), -1)
    cv2.circle(rgba, (85, 44), 8, (248, 244, 200, 255), -1)

    # Arms.
    cv2.rectangle(rgba, (34, 98), (58, 140), (95, 115, 165, 255), -1)
    cv2.rectangle(rgba, (112, 98), (136, 140), (95, 115, 165, 255), -1)
    return rgba


def test_face_validation_accepts_real_character_face():
    scene = _scene_for("Isaki-Riona_pr-img_01_a.png")
    validation = scene.metadata["character"]["structure"]["metadata"]["face_validation"]

    assert validation["accepted"] is True
    assert validation["confidence"] >= validation["threshold"]
    assert validation["eye_count"] >= 1


def test_face_validation_rejects_false_face_candidate(tmp_path: Path):
    image_path = tmp_path / "false_face.png"
    _write_rgba(image_path, _make_false_face_image())

    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
    )
    scene = minimalize(image_path, cfg)
    validation = scene.metadata["character"]["structure"]["metadata"]["face_validation"]
    details = scene.metadata["character"]["details"]["face"]

    assert validation["accepted"] is False
    assert len(validation["reasons"]) >= 1
    assert details["shape_count"] == 0
    assert details["enabled"] is False
    assert not any(p["part_type"] == "face" for p in scene.metadata["character"]["structure"]["parts"])


def test_face_validation_can_be_disabled(tmp_path: Path):
    image_path = tmp_path / "false_face_no_gate.png"
    _write_rgba(image_path, _make_false_face_image())

    cfg = MinimalizeConfig.from_level(
        4,
        analysis_max_side=220,
        target_max_shapes=28,
        line_mode="none",
        enable_auto_retry=False,
        enable_face_primitives=True,
        enable_face_validation=False,
    )
    scene = minimalize(image_path, cfg)
    validation = scene.metadata["character"]["structure"]["metadata"]["face_validation"]

    assert validation["accepted"] is True
    assert any(p["part_type"] == "face" for p in scene.metadata["character"]["structure"]["parts"])
