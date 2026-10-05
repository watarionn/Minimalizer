from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import cv2
import numpy as np

from .ir import (
    AbstractionPlan,
    AbstractionPolicy,
    SemanticPart,
    VisualRole,
)
from .face_neutralization import neutralize_face_policy


@dataclass(frozen=True)
class FaceFeatureEvidence:
    parts: tuple[SemanticPart, ...]
    paired_eye_like: bool
    mouth_like: bool
    micro_contrast_ratio: float

    def to_dict(self) -> dict:
        return {
            "paired_eye_like": self.paired_eye_like,
            "mouth_like": self.mouth_like,
            "micro_contrast_ratio": round(float(self.micro_contrast_ratio), 6),
            "parts": [part.to_dict() for part in sorted(self.parts, key=lambda item: item.id)],
        }


def _bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    ys, xs = np.where(mask)
    if xs.size == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _normalized_bbox(
    x: int,
    y: int,
    width: int,
    height: int,
    image_width: int,
    image_height: int,
) -> tuple[float, float, float, float]:
    return (
        x / float(image_width),
        y / float(image_height),
        (x + width) / float(image_width),
        (y + height) / float(image_height),
    )


def _feature_part(
    feature_id: str,
    bbox: tuple[int, int, int, int],
    *,
    image_width: int,
    image_height: int,
    confidence: float,
    evidence_ref: str,
) -> SemanticPart:
    x, y, width, height = bbox
    return SemanticPart(
        id=f"facial_feature:{feature_id}",
        category="facial_feature",
        subcategory=feature_id,
        bbox=_normalized_bbox(x, y, width, height, image_width, image_height),
        confidence=max(0.0, min(1.0, confidence)),
        visual_role=VisualRole.INTERNAL_DETAIL,
        importance=0.0,
        abstraction_policy=AbstractionPolicy.SUPPRESS,
        evidence_refs=(evidence_ref,),
    )


def detect_facial_feature_evidence(
    rgb: np.ndarray,
    face_mask: np.ndarray,
) -> FaceFeatureEvidence:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("rgb must be HxWx3")
    if face_mask.ndim != 2 or face_mask.shape != rgb.shape[:2]:
        raise ValueError("face_mask must match rgb dimensions")

    face = np.asarray(face_mask).astype(bool)
    face_box = _bbox(face)
    if face_box is None:
        return FaceFeatureEvidence((), False, False, 0.0)

    x0, y0, x1, y1 = face_box
    face_width = max(x1 - x0, 1)
    face_height = max(y1 - y0, 1)
    face_area = max(int(np.count_nonzero(face)), 1)

    kernel_size = max(3, int(round(min(face_width, face_height) * 0.06)))
    if kernel_size % 2 == 0:
        kernel_size += 1
    inner = cv2.erode(
        face.astype(np.uint8),
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)),
    ).astype(bool)
    if not np.any(inner):
        inner = face

    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    local_mean = cv2.GaussianBlur(gray, (0, 0), sigmaX=max(1.0, min(face_width, face_height) * 0.035))
    dark_contrast = local_mean - gray
    candidate = (dark_contrast >= 10.0) & inner

    minimum_area = max(2, int(round(face_area * 0.0015)))
    maximum_area = max(minimum_area, int(round(face_area * 0.11)))
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(
        candidate.astype(np.uint8),
        8,
    )

    components: list[dict[str, float | int]] = []
    for label in range(1, count):
        x, y, width, height, area = [int(value) for value in stats[label]]
        if area < minimum_area or area > maximum_area:
            continue
        cx, cy = [float(value) for value in centroids[label]]
        rel_x = (cx - x0) / face_width
        rel_y = (cy - y0) / face_height
        component_mask = labels == label
        strength = float(np.mean(dark_contrast[component_mask]))
        components.append(
            {
                "label": label,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "area": area,
                "cx": cx,
                "cy": cy,
                "rel_x": rel_x,
                "rel_y": rel_y,
                "strength": strength,
            }
        )

    eye_candidates = [
        item
        for item in components
        if 0.12 <= float(item["rel_y"]) <= 0.58
        and 0.08 <= float(item["rel_x"]) <= 0.92
        and int(item["width"]) <= max(3, int(round(face_width * 0.32)))
        and int(item["height"]) <= max(3, int(round(face_height * 0.22)))
    ]

    best_pair: tuple[dict[str, float | int], dict[str, float | int]] | None = None
    best_pair_score = -1.0
    for index, left in enumerate(eye_candidates):
        for right in eye_candidates[index + 1 :]:
            if float(left["cx"]) > float(right["cx"]):
                left, right = right, left
            separation = (float(right["cx"]) - float(left["cx"])) / face_width
            vertical_delta = abs(float(right["cy"]) - float(left["cy"])) / face_height
            area_ratio = max(float(left["area"]), float(right["area"])) / max(
                min(float(left["area"]), float(right["area"])),
                1.0,
            )
            if not (0.16 <= separation <= 0.68):
                continue
            if vertical_delta > 0.14 or area_ratio > 3.2:
                continue
            symmetry = 1.0 - min(vertical_delta / 0.14, 1.0)
            strength = min(
                (float(left["strength"]) + float(right["strength"])) / 40.0,
                1.0,
            )
            score = symmetry * 0.55 + strength * 0.45
            if score > best_pair_score:
                best_pair_score = score
                best_pair = (left, right)

    mouth_candidates = [
        item
        for item in components
        if 0.48 <= float(item["rel_y"]) <= 0.86
        and 0.14 <= float(item["rel_x"]) <= 0.86
        and int(item["width"]) >= max(3, int(item["height"]) * 2)
        and int(item["width"]) <= max(4, int(round(face_width * 0.62)))
    ]
    mouth = max(
        mouth_candidates,
        key=lambda item: (
            float(item["strength"]) * min(int(item["width"]) / face_width, 1.0),
            int(item["area"]),
        ),
        default=None,
    )

    parts: list[SemanticPart] = []
    if best_pair is not None:
        for side, item in zip(("eye_left", "eye_right"), best_pair):
            parts.append(
                _feature_part(
                    side,
                    (
                        int(item["x"]),
                        int(item["y"]),
                        int(item["width"]),
                        int(item["height"]),
                    ),
                    image_width=rgb.shape[1],
                    image_height=rgb.shape[0],
                    confidence=min(1.0, 0.5 + best_pair_score * 0.5),
                    evidence_ref="derived:paired-dark-face-islands",
                )
            )

    if mouth is not None:
        mouth_confidence = min(1.0, 0.4 + float(mouth["strength"]) / 35.0)
        parts.append(
            _feature_part(
                "mouth_like",
                (
                    int(mouth["x"]),
                    int(mouth["y"]),
                    int(mouth["width"]),
                    int(mouth["height"]),
                ),
                image_width=rgb.shape[1],
                image_height=rgb.shape[0],
                confidence=mouth_confidence,
                evidence_ref="derived:horizontal-dark-face-component",
            )
        )

    micro_ratio = float(np.count_nonzero((dark_contrast >= 7.0) & inner)) / max(
        float(np.count_nonzero(inner)),
        1.0,
    )
    return FaceFeatureEvidence(
        parts=tuple(sorted(parts, key=lambda part: part.id)),
        paired_eye_like=best_pair is not None,
        mouth_like=mouth is not None,
        micro_contrast_ratio=micro_ratio,
    )


def attach_facial_feature_evidence(
    plan: AbstractionPlan,
    evidence: FaceFeatureEvidence,
) -> AbstractionPlan:
    retained = tuple(
        part for part in plan.parts if not part.id.startswith("facial_feature:")
    )
    combined = AbstractionPlan(
        parts=retained + evidence.parts,
        schema_version=plan.schema_version,
    )
    return neutralize_face_policy(combined)
