from __future__ import annotations

from dataclasses import dataclass
import cv2
import numpy as np

from ..models import Shape
from .models import CharacterPartCandidate, CharacterStructure
from .primitive_fit import fit_best_primitive


@dataclass
class HeadFeatureReport:
    enabled: bool = False
    candidate_pixels: int = 0
    selected_shapes: int = 0
    colors: list[tuple[int, int, int]] | None = None

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "candidate_pixels": self.candidate_pixels,
            "selected_shapes": self.selected_shapes,
            "colors": [list(c) for c in (self.colors or [])],
        }


def _part(structure: CharacterStructure, name: str) -> CharacterPartCandidate | None:
    return next((p for p in structure.parts if str(p.part_type) == name), None)


def _representative_color(image_rgb: np.ndarray, mask: np.ndarray) -> tuple[int, int, int]:
    pixels = image_rgb[mask > 0]
    if pixels.size == 0:
        return (0, 0, 0)
    bins = (pixels.astype(np.uint16) // 24).astype(np.int16)
    keys = bins[:, 0] * 121 + bins[:, 1] * 11 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    key = values[int(np.argmax(counts))]
    selected = keys == key
    return tuple(int(v) for v in np.median(pixels[selected], axis=0))

def build_head_feature_shapes(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    *,
    start_id: int,
) -> tuple[list[Shape], HeadFeatureReport]:
    head = _part(structure, "head")
    face = _part(structure, "face")
    hair = _part(structure, "hair")
    if head is None or face is None or hair is None:
        return [], HeadFeatureReport()

    h, w = image_rgb.shape[:2]
    x, y, bw, bh = head.bbox
    x0 = max(0, int(x - bw * 0.18))
    x1 = min(w, int(x + bw * 1.18))
    y0 = max(0, int(y - bh * 0.45))
    y1 = min(h, int(y + bh * 0.72))
    roi = np.zeros((h, w), dtype=np.uint8)
    roi[y0:y1, x0:x1] = 1
    roi = roi * (structure.subject_mask > 0).astype(np.uint8)
    roi[face.mask > 0] = 0

    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    face_ref = np.median(lab[face.mask > 0], axis=0)
    hair_ref = np.median(lab[hair.mask > 0], axis=0)
    face_distance = np.linalg.norm(lab - face_ref[None, None, :], axis=2)
    hair_distance = np.linalg.norm(lab - hair_ref[None, None, :], axis=2)
    border = np.concatenate([image_rgb[0], image_rgb[-1], image_rgb[:, 0], image_rgb[:, -1]], axis=0)
    background_rgb = np.median(border, axis=0).astype(np.uint8)
    background_lab = cv2.cvtColor(background_rgb.reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    background_distance = np.linalg.norm(lab - background_lab[None, None, :], axis=2)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    candidate = (
        (roi > 0)
        & (saturation >= 130)
        & (value >= 80)
        & (face_distance >= 26.0)
        & (hair_distance >= 18.0)
        & (background_distance >= 24.0)
    ).astype(np.uint8)
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_CLOSE, np.ones((2, 2), np.uint8))
    candidate = cv2.morphologyEx(candidate, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))

    count, labels, stats, _ = cv2.connectedComponentsWithStats(candidate, connectivity=8)
    head_area = max(float(head.area), 1.0)
    components = []
    for label in range(1, count):
        area = int(stats[label, cv2.CC_STAT_AREA])
        if area < max(4, int(head_area * 0.003)) or area > head_area * 0.08:
            continue
        comp = (labels == label).astype(np.uint8)
        sat_score = float(saturation[comp > 0].mean()) / 255.0
        separation = float(np.minimum(face_distance, hair_distance)[comp > 0].mean()) / 60.0
        score = 0.45 * min(1.0, area / max(head_area * 0.04, 1.0)) + 0.30 * sat_score + 0.25 * min(1.0, separation)
        components.append((score, area, comp))
    components.sort(key=lambda item: (item[0], item[1]), reverse=True)
    shapes: list[Shape] = []
    colors: list[tuple[int, int, int]] = []
    next_id = start_id
    selected_labs: list[np.ndarray] = []
    for _, _, comp in components:
        if len(shapes) >= 3:
            break
        color = _representative_color(image_rgb, comp)
        if sum(color) / 3.0 < 70.0:
            continue
        color_rgb = np.asarray(color, dtype=np.uint8).reshape(1, 1, 3)
        color_lab = cv2.cvtColor(color_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        if any(float(np.linalg.norm(color_lab - prior)) < 20.0 for prior in selected_labs):
            continue
        fit = fit_best_primitive(
            comp,
            allowed=("triangle", "rotated_rect", "polygon"),
            polygon_vertices=(3, 4, 5, 6),
        )
        if fit is None:
            continue
        selected_labs.append(color_lab)
        kwargs = dict(
            id=next_id,
            fill_color=color,
            z_index=28650 + len(shapes),
            importance=1.0,
            source_role="rinka_macro:accessory:feature",
            layer_name="character_hair_detail",
            semantic_type="rinka_macro_head_feature",
            character_part="accessory",
            part_confidence=0.90,
        )
        if fit.shape_type == "ellipse":
            shape = Shape(shape_type="ellipse", points=[], cx=fit.cx, cy=fit.cy, rx=fit.rx, ry=fit.ry, **kwargs)
        else:
            shape = Shape(shape_type="polygon", points=list(fit.points or []), **kwargs)
        shapes.append(shape)
        colors.append(color)
        next_id += 1

    report = HeadFeatureReport(
        enabled=bool(shapes),
        candidate_pixels=int(candidate.sum()),
        selected_shapes=len(shapes),
        colors=colors,
    )
    return shapes, report
