from __future__ import annotations

from dataclasses import dataclass, asdict
import cv2
import numpy as np

from ..models import Shape
from .models import CharacterStructure
from .part_types import CharacterPartType


@dataclass(slots=True)
class LimbRefineItem:
    part: str
    before_iou: float
    after_iou: float
    refined: bool
    before_area_ratio: float
    after_area_ratio: float


@dataclass(slots=True)
class LimbRefineReport:
    score: float
    refined_count: int
    items: list[LimbRefineItem]
    diagnostics: dict

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _shape_mask(shape: Shape, hw: tuple[int, int]) -> np.ndarray:
    out = np.zeros(hw, np.uint8)
    if shape.points and len(shape.points) >= 3:
        cv2.fillPoly(out, [np.asarray(shape.points, np.int32)], 255)
    return out


def _iou(a: np.ndarray, b: np.ndarray) -> float:
    aa, bb = a > 0, b > 0
    inter = int(np.count_nonzero(aa & bb))
    union = int(np.count_nonzero(aa | bb))
    return 1.0 if union == 0 else inter / union


def _simplified_source(mask: np.ndarray, max_vertices: int = 8) -> list[tuple[float, float]]:
    binary = (mask > 0).astype(np.uint8) * 255
    k = max(3, int(round(min(mask.shape) * 0.004)) * 2 + 1)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return []
    c = max(contours, key=cv2.contourArea)
    peri = max(1.0, float(cv2.arcLength(c, True)))
    eps = peri * 0.018
    approx = cv2.approxPolyDP(c, eps, True)
    while len(approx) > max_vertices and eps < peri * 0.09:
        eps *= 1.22
        approx = cv2.approxPolyDP(c, eps, True)
    if len(approx) < 3:
        return []
    return [(float(p[0][0]), float(p[0][1])) for p in approx]


def refine_limb_shapes(
    body_shapes: list[Shape],
    structure: CharacterStructure,
    *,
    min_iou: float = 0.46,
) -> tuple[list[Shape], LimbRefineReport]:
    """Repair only strongly mismatched limb silhouettes without adding Shapes."""
    type_map = {
        "left_arm": CharacterPartType.LEFT_ARM,
        "right_arm": CharacterPartType.RIGHT_ARM,
        "left_leg": CharacterPartType.LEFT_LEG,
        "right_leg": CharacterPartType.RIGHT_LEG,
    }
    out: list[Shape] = []
    items: list[LimbRefineItem] = []
    hw = structure.subject_mask.shape[:2]
    for shape in body_shapes:
        ptype = type_map.get(shape.character_part)
        part = structure.first_part(ptype) if ptype is not None else None
        if part is None or shape.source_role != "character_limb_base":
            out.append(shape)
            continue
        source = (part.mask > 0).astype(np.uint8) * 255
        before = _shape_mask(shape, hw)
        biou = _iou(before, source)
        src_area = max(1, int(np.count_nonzero(source)))
        barea = int(np.count_nonzero(before))
        before_ratio = barea / src_area
        refined = False
        new_shape = shape
        # Only repair clear geometric failures.  Good simplified limbs stay untouched.
        if biou < min_iou or before_ratio < 0.58 or before_ratio > 1.55:
            pts = _simplified_source(source)
            if len(pts) >= 3:
                candidate = Shape(**{**shape.__dict__, "points": pts})
                cmask = _shape_mask(candidate, hw)
                ciou = _iou(cmask, source)
                # Require a meaningful win so the source contour does not replace
                # an already useful abstract primitive for tiny numerical gains.
                if ciou >= biou + 0.08:
                    new_shape = candidate
                    refined = True
        after = _shape_mask(new_shape, hw)
        aiou = _iou(after, source)
        after_ratio = int(np.count_nonzero(after)) / src_area
        items.append(LimbRefineItem(shape.character_part, biou, aiou, refined, before_ratio, after_ratio))
        out.append(new_shape)
    score = float(np.mean([x.after_iou for x in items])) if items else 1.0
    return out, LimbRefineReport(
        score=score,
        refined_count=sum(1 for x in items if x.refined),
        items=items,
        diagnostics={
            "phase": "12.1",
            "principle": "repair severe limb silhouette mismatch without adding detail",
            "min_iou": float(min_iou),
            "shape_count_changed": False,
        },
    )
