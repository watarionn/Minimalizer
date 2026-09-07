from __future__ import annotations

from dataclasses import asdict, dataclass, field
import math

import cv2
import numpy as np

from ..models import Scene, Shape
from .heuristics import mask_bbox, mask_centroid
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType


@dataclass(slots=True)
class FaceGeometryMetrics:
    score: float
    area_ratio_score: float
    center_score: float
    aspect_score: float
    eye_span_score: float | None
    mouth_position_score: float | None
    mask_iou_score: float
    head_area_ratio_score: float

    source_face_area: int
    generated_face_area: int
    source_face_bbox: tuple[int, int, int, int]
    generated_face_bbox: tuple[int, int, int, int]
    source_face_center: tuple[float, float]
    generated_face_center: tuple[float, float]

    source_eye_span_ratio: float | None = None
    generated_eye_span_ratio: float | None = None
    source_mouth_relative: tuple[float, float] | None = None
    generated_mouth_relative: tuple[float, float] | None = None

    applicable: bool = True
    passed: bool = True
    retry_reasons: list[str] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


def _clamp01(value: float) -> float:
    return float(np.clip(value, 0.0, 1.0))


def _relative_ratio_score(
    ratio: float,
    *,
    tolerance: float,
) -> float:
    ratio = max(float(ratio), 1e-6)
    tolerance = max(float(tolerance), 0.02)
    error = abs(math.log(ratio))
    sigma = max(math.log1p(tolerance), 1e-6)
    # At the configured tolerance this is roughly 0.78, then falls smoothly.
    return _clamp01(math.exp(-0.25 * (error / sigma) ** 2))


def _point_score(
    a: tuple[float, float],
    b: tuple[float, float],
    *,
    normalizer: float,
    tolerance: float,
) -> float:
    normalizer = max(float(normalizer), 1.0)
    tolerance = max(float(tolerance), 0.02)
    distance = math.hypot(a[0] - b[0], a[1] - b[1]) / normalizer
    return _clamp01(math.exp(-0.45 * (distance / tolerance) ** 2))


def _bbox_aspect(bbox: tuple[int, int, int, int]) -> float:
    return float(bbox[2]) / max(float(bbox[3]), 1.0)


def _shape_center(shape: Shape) -> tuple[float, float] | None:
    if shape.shape_type in {"circle", "ellipse"}:
        if shape.cx is None or shape.cy is None:
            return None
        return float(shape.cx), float(shape.cy)
    if shape.shape_type == "rectangle":
        if None in {shape.x, shape.y, shape.width, shape.height}:
            return None
        return (
            float(shape.x + shape.width / 2.0),
            float(shape.y + shape.height / 2.0),
        )
    if shape.points:
        xs = [p[0] for p in shape.points]
        ys = [p[1] for p in shape.points]
        return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))
    return None


def _shape_to_mask(scene: Scene, shape: Shape) -> np.ndarray:
    mask = np.zeros((scene.height, scene.width), dtype=np.uint8)

    if shape.shape_type == "polygon" and len(shape.points) >= 3:
        pts = np.asarray(shape.points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
    elif shape.shape_type == "rectangle":
        if None not in {shape.x, shape.y, shape.width, shape.height}:
            x0 = int(round(shape.x))
            y0 = int(round(shape.y))
            x1 = int(round(shape.x + shape.width))
            y1 = int(round(shape.y + shape.height))
            cv2.rectangle(mask, (x0, y0), (x1, y1), 255, thickness=-1)
    elif shape.shape_type == "circle":
        if None not in {shape.cx, shape.cy, shape.rx}:
            cv2.circle(
                mask,
                (int(round(shape.cx)), int(round(shape.cy))),
                max(1, int(round(shape.rx))),
                255,
                thickness=-1,
            )
    elif shape.shape_type == "ellipse":
        if None not in {shape.cx, shape.cy, shape.rx, shape.ry}:
            cv2.ellipse(
                mask,
                (int(round(shape.cx)), int(round(shape.cy))),
                (
                    max(1, int(round(shape.rx))),
                    max(1, int(round(shape.ry))),
                ),
                0.0,
                0.0,
                360.0,
                255,
                thickness=-1,
            )
    elif shape.shape_type == "line" and len(shape.points) >= 2:
        pts = np.asarray(shape.points, dtype=np.int32)
        cv2.polylines(
            mask,
            [pts],
            False,
            255,
            thickness=max(1, int(round(shape.stroke_width or 1.0))),
        )

    return mask


def _source_transform(
    scene: Scene,
    *,
    canvas_padding: float,
) -> tuple[float, float, float]:
    layout = scene.metadata.get("character", {}).get("layout", {})
    if layout.get("enabled", False):
        return (
            float(layout.get("scale", 1.0)),
            float(layout.get("translate_x", 0.0)),
            float(layout.get("translate_y", 0.0)),
        )

    padding = float(np.clip(canvas_padding, 0.0, 0.40))
    scale = 1.0 - 2.0 * padding
    return scale, scene.width * padding, scene.height * padding


def _transform_mask(
    mask: np.ndarray,
    scene: Scene,
    *,
    canvas_padding: float,
) -> np.ndarray:
    scale, tx, ty = _source_transform(
        scene,
        canvas_padding=canvas_padding,
    )
    matrix = np.asarray(
        [
            [scale, 0.0, tx],
            [0.0, scale, ty],
        ],
        dtype=np.float32,
    )
    return cv2.warpAffine(
        (mask > 0).astype(np.uint8) * 255,
        matrix,
        (scene.width, scene.height),
        flags=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=0,
    )


def _transform_point(
    point: tuple[float, float] | None,
    scene: Scene,
    *,
    canvas_padding: float,
) -> tuple[float, float] | None:
    if point is None:
        return None
    scale, tx, ty = _source_transform(
        scene,
        canvas_padding=canvas_padding,
    )
    return (
        float(point[0] * scale + tx),
        float(point[1] * scale + ty),
    )


def _face_layout_metadata(scene: Scene) -> dict:
    return (
        scene.metadata.get("character", {})
        .get("details", {})
        .get("face", {})
        .get("layout", {})
        or {}
    )


def _source_eye_points(
    scene: Scene,
    *,
    canvas_padding: float,
) -> dict[str, tuple[float, float] | None]:
    layout = _face_layout_metadata(scene)

    def point(key: str) -> tuple[float, float] | None:
        raw = layout.get(key)
        if raw is None:
            return None
        return _transform_point(
            (float(raw[0]), float(raw[1])),
            scene,
            canvas_padding=canvas_padding,
        )

    return {
        "left": point("left_eye"),
        "right": point("right_eye"),
    }


def _source_mouth_point(
    scene: Scene,
    *,
    canvas_padding: float,
) -> tuple[float, float] | None:
    raw = _face_layout_metadata(scene).get("mouth")
    if raw is None:
        return None
    return _transform_point(
        (float(raw[0]), float(raw[1])),
        scene,
        canvas_padding=canvas_padding,
    )


def _normalized_point(
    point: tuple[float, float] | None,
    bbox: tuple[int, int, int, int],
) -> tuple[float, float] | None:
    if point is None:
        return None
    x, y, w, h = bbox
    return (
        (point[0] - x) / max(float(w), 1.0),
        (point[1] - y) / max(float(h), 1.0),
    )


def _eye_span_ratio(
    eyes: dict[str, tuple[float, float] | None],
    bbox: tuple[int, int, int, int],
) -> float | None:
    left = eyes.get("left")
    right = eyes.get("right")
    if left is None or right is None:
        return None
    return abs(right[0] - left[0]) / max(float(bbox[2]), 1.0)


def extract_generated_face_mask(scene: Scene) -> np.ndarray:
    base = [
        s for s in scene.shapes
        if s.character_part == "face"
        and s.source_role == "character_face_base"
    ]
    if not base:
        return np.zeros((scene.height, scene.width), dtype=np.uint8)
    union = np.zeros((scene.height, scene.width), dtype=np.uint8)
    for shape in base:
        union = cv2.bitwise_or(union, _shape_to_mask(scene, shape))
    return union


def extract_generated_eye_points(
    scene: Scene,
) -> dict[str, tuple[float, float] | None]:
    centers = []
    for shape in scene.shapes:
        if shape.character_part != "face":
            continue
        if shape.source_role != "character_eye":
            continue
        center = _shape_center(shape)
        if center is not None:
            centers.append(center)

    centers.sort(key=lambda p: p[0])
    if not centers:
        return {"left": None, "right": None}
    if len(centers) == 1:
        face_mask = extract_generated_face_mask(scene)
        if np.count_nonzero(face_mask) > 0:
            fx, _, fw, _ = mask_bbox(face_mask)
            if centers[0][0] < fx + fw / 2.0:
                return {"left": centers[0], "right": None}
        return {"left": None, "right": centers[0]}

    return {"left": centers[0], "right": centers[-1]}


def extract_generated_mouth_point(
    scene: Scene,
) -> tuple[float, float] | None:
    for shape in scene.shapes:
        if shape.character_part != "face":
            continue
        if shape.source_role != "character_mouth":
            continue
        return _shape_center(shape)
    return None


def score_face_area_ratio(
    source_face_area: int,
    generated_face_area: int,
    *,
    tolerance: float,
) -> float:
    ratio = generated_face_area / max(float(source_face_area), 1.0)
    return _relative_ratio_score(ratio, tolerance=tolerance)


def score_face_center_alignment(
    source_center: tuple[float, float],
    generated_center: tuple[float, float],
    *,
    face_bbox: tuple[int, int, int, int],
    tolerance: float,
) -> float:
    diagonal = math.hypot(face_bbox[2], face_bbox[3])
    return _point_score(
        source_center,
        generated_center,
        normalizer=diagonal,
        tolerance=tolerance,
    )


def score_face_aspect_ratio(
    source_bbox: tuple[int, int, int, int],
    generated_bbox: tuple[int, int, int, int],
    *,
    tolerance: float,
) -> float:
    ratio = _bbox_aspect(generated_bbox) / max(_bbox_aspect(source_bbox), 1e-6)
    return _relative_ratio_score(ratio, tolerance=tolerance)


def score_eye_span_ratio(
    source_eye_points: dict[str, tuple[float, float] | None],
    generated_eye_points: dict[str, tuple[float, float] | None],
    source_bbox: tuple[int, int, int, int],
    generated_bbox: tuple[int, int, int, int],
    *,
    tolerance: float,
) -> float | None:
    source_ratio = _eye_span_ratio(source_eye_points, source_bbox)
    generated_ratio = _eye_span_ratio(generated_eye_points, generated_bbox)
    if source_ratio is None or generated_ratio is None:
        return None
    return _relative_ratio_score(
        generated_ratio / max(source_ratio, 1e-6),
        tolerance=tolerance,
    )


def score_mouth_relative_position(
    source_mouth_point: tuple[float, float] | None,
    generated_mouth_point: tuple[float, float] | None,
    source_bbox: tuple[int, int, int, int],
    generated_bbox: tuple[int, int, int, int],
    *,
    tolerance: float,
) -> float | None:
    source_relative = _normalized_point(source_mouth_point, source_bbox)
    generated_relative = _normalized_point(generated_mouth_point, generated_bbox)
    if source_relative is None or generated_relative is None:
        return None
    return _point_score(
        source_relative,
        generated_relative,
        normalizer=1.0,
        tolerance=tolerance,
    )


def score_face_mask_iou(
    source_mask: np.ndarray,
    generated_mask: np.ndarray,
) -> float:
    source = (source_mask > 0).astype(np.uint8)
    generated = (generated_mask > 0).astype(np.uint8)
    if np.count_nonzero(source) == 0 or np.count_nonzero(generated) == 0:
        return 0.0

    sb = mask_bbox(source * 255)
    scale_hint = max(1, int(round(min(sb[2], sb[3]) * 0.035)))
    k = scale_hint * 2 + 1
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))

    soft_source = cv2.dilate(source, kernel)
    soft_generated = cv2.dilate(generated, kernel)

    raw_inter = np.count_nonzero((source > 0) & (generated > 0))
    raw_union = np.count_nonzero((source > 0) | (generated > 0))
    raw_iou = raw_inter / max(raw_union, 1)

    soft_inter = np.count_nonzero((soft_source > 0) & (soft_generated > 0))
    soft_union = np.count_nonzero((soft_source > 0) | (soft_generated > 0))
    soft_iou = soft_inter / max(soft_union, 1)

    return float(np.clip(raw_iou * 0.35 + soft_iou * 0.65, 0.0, 1.0))


def _head_area_ratio_score(
    source_face_area: int,
    generated_face_area: int,
    source_head_area: int,
    generated_head_area: int,
    *,
    tolerance: float,
) -> float:
    source_ratio = source_face_area / max(float(source_head_area), 1.0)
    generated_ratio = generated_face_area / max(float(generated_head_area), 1.0)
    return _relative_ratio_score(
        generated_ratio / max(source_ratio, 1e-6),
        tolerance=tolerance,
    )


def compute_face_geometry_metrics(
    source_face_part: CharacterPartCandidate,
    generated_face_mask: np.ndarray,
    *,
    source_face_mask: np.ndarray | None = None,
    source_head_mask: np.ndarray | None = None,
    generated_head_mask: np.ndarray | None = None,
    source_eye_points: dict[str, tuple[float, float] | None] | None = None,
    generated_eye_points: dict[str, tuple[float, float] | None] | None = None,
    source_mouth_point: tuple[float, float] | None = None,
    generated_mouth_point: tuple[float, float] | None = None,
    area_ratio_tolerance: float = 0.30,
    center_tolerance: float = 0.18,
    aspect_tolerance: float = 0.28,
    eye_span_tolerance: float = 0.30,
    mouth_offset_tolerance: float = 0.26,
    min_score: float = 0.72,
) -> FaceGeometryMetrics:
    source_mask = source_face_mask if source_face_mask is not None else source_face_part.mask
    source_mask = (source_mask > 0).astype(np.uint8) * 255
    generated_mask = (generated_face_mask > 0).astype(np.uint8) * 255

    source_area = int(np.count_nonzero(source_mask))
    generated_area = int(np.count_nonzero(generated_mask))

    source_bbox = mask_bbox(source_mask) if source_area > 0 else source_face_part.bbox
    generated_bbox = mask_bbox(generated_mask) if generated_area > 0 else (0, 0, 1, 1)
    source_center = mask_centroid(source_mask) if source_area > 0 else source_face_part.centroid
    generated_center = mask_centroid(generated_mask) if generated_area > 0 else (0.0, 0.0)

    area_score = score_face_area_ratio(source_area, generated_area, tolerance=area_ratio_tolerance)
    center_score = score_face_center_alignment(source_center, generated_center, face_bbox=source_bbox, tolerance=center_tolerance)
    aspect_score = score_face_aspect_ratio(source_bbox, generated_bbox, tolerance=aspect_tolerance)

    source_eyes = source_eye_points or {"left": None, "right": None}
    generated_eyes = generated_eye_points or {"left": None, "right": None}
    eye_score = score_eye_span_ratio(source_eyes, generated_eyes, source_bbox, generated_bbox, tolerance=eye_span_tolerance)
    mouth_score = score_mouth_relative_position(source_mouth_point, generated_mouth_point, source_bbox, generated_bbox, tolerance=mouth_offset_tolerance)
    mask_iou = score_face_mask_iou(source_mask, generated_mask)

    source_head = ((source_head_mask > 0).astype(np.uint8) * 255) if source_head_mask is not None else None
    generated_head = ((generated_head_mask > 0).astype(np.uint8) * 255) if generated_head_mask is not None else None
    if source_head is not None and generated_head is not None and np.count_nonzero(source_head) > 0 and np.count_nonzero(generated_head) > 0:
        head_score = _head_area_ratio_score(
            source_area,
            generated_area,
            int(np.count_nonzero(source_head)),
            int(np.count_nonzero(generated_head)),
            tolerance=area_ratio_tolerance,
        )
    else:
        head_score = area_score

    components: list[tuple[float, float]] = [
        (area_score, 0.17),
        (center_score, 0.17),
        (aspect_score, 0.13),
        (mask_iou, 0.15),
        (head_score, 0.10),
    ]
    if eye_score is not None:
        components.append((eye_score, 0.16))
    if mouth_score is not None:
        components.append((mouth_score, 0.12))

    weight_sum = sum(weight for _, weight in components)
    score = sum(value * weight for value, weight in components) / max(weight_sum, 1e-9)

    source_eye_span = _eye_span_ratio(source_eyes, source_bbox)
    generated_eye_span = _eye_span_ratio(generated_eyes, generated_bbox)
    source_mouth_rel = _normalized_point(source_mouth_point, source_bbox)
    generated_mouth_rel = _normalized_point(generated_mouth_point, generated_bbox)

    metrics = FaceGeometryMetrics(
        score=float(np.clip(score, 0.0, 1.0)),
        area_ratio_score=area_score,
        center_score=center_score,
        aspect_score=aspect_score,
        eye_span_score=eye_score,
        mouth_position_score=mouth_score,
        mask_iou_score=mask_iou,
        head_area_ratio_score=head_score,
        source_face_area=source_area,
        generated_face_area=generated_area,
        source_face_bbox=source_bbox,
        generated_face_bbox=generated_bbox,
        source_face_center=(float(source_center[0]), float(source_center[1])),
        generated_face_center=(float(generated_center[0]), float(generated_center[1])),
        source_eye_span_ratio=source_eye_span,
        generated_eye_span_ratio=generated_eye_span,
        source_mouth_relative=source_mouth_rel,
        generated_mouth_relative=generated_mouth_rel,
        applicable=True,
        passed=float(score) >= min_score,
        diagnostics={
            "generated_to_source_area_ratio": generated_area / max(float(source_area), 1.0),
            "source_bbox_aspect": _bbox_aspect(source_bbox),
            "generated_bbox_aspect": _bbox_aspect(generated_bbox),
            "component_weights": {
                "area_ratio": 0.17,
                "center": 0.17,
                "aspect": 0.13,
                "eye_span": 0.16 if eye_score is not None else 0.0,
                "mouth_position": 0.12 if mouth_score is not None else 0.0,
                "mask_iou": 0.15,
                "head_area_ratio": 0.10,
            },
        },
    )
    metrics.retry_reasons = face_geometry_retry_reasons(metrics, min_score=min_score)
    return metrics


def face_geometry_retry_reasons(
    metrics: FaceGeometryMetrics,
    *,
    min_score: float,
) -> list[str]:
    return ["face_geometry_low"] if metrics.score < min_score else []


def evaluate_face_geometry(
    scene: Scene,
    structure: CharacterStructure,
    *,
    min_score: float = 0.72,
    area_ratio_tolerance: float = 0.30,
    center_tolerance: float = 0.18,
    aspect_tolerance: float = 0.28,
    eye_span_tolerance: float = 0.30,
    mouth_offset_tolerance: float = 0.26,
    canvas_padding: float = 0.05,
) -> FaceGeometryMetrics | None:
    face = structure.first_part(CharacterPartType.FACE)
    if face is None:
        return None

    validation = structure.metadata.get("face_validation") or face.metadata.get("validation") or {}
    if validation and not bool(validation.get("accepted", False)):
        return None

    generated_face_mask = extract_generated_face_mask(scene)
    source_face_mask = _transform_mask(face.mask, scene, canvas_padding=canvas_padding)

    head = structure.first_part(CharacterPartType.HEAD)
    source_head_mask = None
    generated_head_mask = None
    if head is not None:
        source_head_mask = _transform_mask(head.mask, scene, canvas_padding=canvas_padding)
        # No dedicated HEAD Shape exists yet. The transformed source head is the
        # denominator for the generated face/head area ratio.
        generated_head_mask = source_head_mask.copy()

    source_eyes = _source_eye_points(scene, canvas_padding=canvas_padding)
    generated_eyes = extract_generated_eye_points(scene)
    source_mouth = _source_mouth_point(scene, canvas_padding=canvas_padding)
    generated_mouth = extract_generated_mouth_point(scene)

    return compute_face_geometry_metrics(
        face,
        generated_face_mask,
        source_face_mask=source_face_mask,
        source_head_mask=source_head_mask,
        generated_head_mask=generated_head_mask,
        source_eye_points=source_eyes,
        generated_eye_points=generated_eyes,
        source_mouth_point=source_mouth,
        generated_mouth_point=generated_mouth,
        area_ratio_tolerance=area_ratio_tolerance,
        center_tolerance=center_tolerance,
        aspect_tolerance=aspect_tolerance,
        eye_span_tolerance=eye_span_tolerance,
        mouth_offset_tolerance=mouth_offset_tolerance,
        min_score=min_score,
    )
