from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ..models import Shape
from .models import CharacterPartCandidate, CharacterStructure
from .head_feature import build_head_feature_shapes
from .primitive_fit import PrimitiveFit, cap_primitive_area, fit_best_primitive
from .semantic_shape_tree import build_semantic_shape_tree


@dataclass
class RinkaMacroReport:
    enabled: bool = False
    reason: str = "disabled"
    generated_shapes: int = 0
    retained_detail_shapes: int = 0
    part_shape_counts: dict[str, int] | None = None
    semantic_tree_nodes: int = 0
    primitive_fits: dict[str, dict] | None = None
    semantic_tree: dict | None = None
    head_features: dict | None = None

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "reason": self.reason,
            "generated_shapes": self.generated_shapes,
            "retained_detail_shapes": self.retained_detail_shapes,
            "part_shape_counts": dict(self.part_shape_counts or {}),
            "semantic_tree_nodes": self.semantic_tree_nodes,
            "primitive_fits": dict(self.primitive_fits or {}),
            "semantic_tree": dict(self.semantic_tree or {}),
            "head_features": dict(self.head_features or {}),
        }


def _part(structure: CharacterStructure, name: str) -> CharacterPartCandidate | None:
    return next((p for p in structure.parts if str(p.part_type) == name), None)


def _coarse_color_groups(
    image_rgb: np.ndarray,
    mask: np.ndarray,
    *,
    max_colors: int,
    min_fraction: float = 0.035,
) -> list[tuple[tuple[int, int, int], np.ndarray, int]]:
    active = mask > 0
    pixels = image_rgb[active]
    if pixels.size == 0:
        return []
    bins = (pixels.astype(np.uint16) // 32).astype(np.int16)
    keys = bins[:, 0] * 64 + bins[:, 1] * 8 + bins[:, 2]
    values, counts = np.unique(keys, return_counts=True)
    order = np.argsort(counts)[::-1]
    groups: list[tuple[tuple[int, int, int], np.ndarray, int]] = []
    flat_active = np.flatnonzero(active)
    for idx in order[: max_colors * 3]:
        selected = keys == values[idx]
        count = int(selected.sum())
        if count < max(6, int(active.sum() * min_fraction)):
            continue
        color = tuple(int(v) for v in np.median(pixels[selected], axis=0))
        group_mask = np.zeros(mask.shape, dtype=np.uint8)
        group_mask.flat[flat_active[selected]] = 1
        kernel = 3
        group_mask = cv2.morphologyEx(
            group_mask,
            cv2.MORPH_CLOSE,
            np.ones((kernel, kernel), np.uint8),
        )
        groups.append((color, group_mask, count))
        if len(groups) >= max_colors:
            break
    return groups


def _largest_contours(
    mask: np.ndarray,
    *,
    max_components: int,
    min_area: float,
) -> list[np.ndarray]:
    contours, _ = cv2.findContours(
        mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    usable = [c for c in contours if cv2.contourArea(c) >= min_area]
    usable.sort(key=cv2.contourArea, reverse=True)
    return usable[:max_components]


def _simplify_contour(contour: np.ndarray, max_vertices: int = 8) -> np.ndarray:
    perimeter = max(cv2.arcLength(contour, True), 1.0)
    epsilon = 0.018 * perimeter
    approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    while len(approx) > max_vertices and epsilon < perimeter * 0.12:
        epsilon *= 1.25
        approx = cv2.approxPolyDP(contour, epsilon, True).reshape(-1, 2)
    return approx


def _shape_from_contour(
    contour: np.ndarray,
    *,
    shape_id: int,
    color: tuple[int, int, int],
    z_index: int,
    semantic_type: str,
    character_part: str,
    source_role: str,
    layer_name: str,
) -> Shape | None:
    approx = _simplify_contour(contour)
    if len(approx) < 3:
        return None
    return Shape(
        id=shape_id,
        shape_type="polygon",
        fill_color=color,
        points=[(float(x), float(y)) for x, y in approx],
        z_index=z_index,
        importance=1.0,
        source_role=source_role,
        layer_name=layer_name,
        semantic_type=semantic_type,
        character_part=character_part,
        part_confidence=0.98,
    )


def _allowed_primitives(part_name: str) -> tuple[str, ...]:
    if part_name == "face":
        return ("ellipse", "polygon")
    if part_name == "outfit":
        return ("trapezoid", "rotated_rect", "polygon")
    if part_name == "hair":
        return ("polygon", "rotated_rect")
    if part_name in {"left_arm", "right_arm", "left_leg", "right_leg"}:
        return ("rotated_rect", "trapezoid", "polygon")
    return ("polygon",)


def _shape_from_fit(fit: PrimitiveFit, **kwargs) -> Shape:
    if fit.shape_type == "ellipse":
        return Shape(shape_type="ellipse", points=[], cx=fit.cx, cy=fit.cy, rx=fit.rx, ry=fit.ry, **kwargs)
    return Shape(shape_type="polygon", points=list(fit.points or []), **kwargs)


def _fit_family(fit: PrimitiveFit) -> str:
    if fit.kind.startswith("polygon_"):
        return "polygon"
    if fit.kind.startswith("trapezoid_"):
        return "trapezoid"
    return fit.kind


def _fit_part_primitive(part_name: str, mask: np.ndarray) -> tuple[PrimitiveFit | None, list[dict]]:
    trials: list[dict] = []
    fits: list[PrimitiveFit] = []
    for family in _allowed_primitives(part_name):
        fit = fit_best_primitive(
            mask,
            allowed=(family,),
            polygon_vertices=(4, 5, 6, 8),
        )
        if fit is not None and part_name == "outfit" and family == "trapezoid":
            fit = cap_primitive_area(fit, mask, 0.079)
        if fit is not None:
            fits.append(fit)
            trials.append(fit.to_dict())
    if not fits:
        return None, trials
    priors = {
        "outfit": {"trapezoid": 0.15, "rotated_rect": 0.06},
        "face": {"ellipse": 0.05},
        "left_arm": {"rotated_rect": 0.05, "trapezoid": 0.03},
        "right_arm": {"rotated_rect": 0.05, "trapezoid": 0.03},
        "left_leg": {"rotated_rect": 0.04, "trapezoid": 0.02},
        "right_leg": {"rotated_rect": 0.04, "trapezoid": 0.02},
    }.get(part_name, {})
    raw_best = max(fits, key=lambda f: f.score)
    adjusted = max(fits, key=lambda f: f.score + priors.get(_fit_family(f), 0.0))
    if adjusted.score < raw_best.score - 0.13:
        adjusted = raw_best
    return adjusted, trials


_PART_SPECS = {
    "hair": dict(max_colors=6, max_components=2, z=24200, accents=2),
    "left_leg": dict(max_colors=5, max_components=2, z=25000, accents=2),
    "right_leg": dict(max_colors=5, max_components=2, z=25020, accents=2),
    "outfit": dict(max_colors=8, max_components=2, z=26200, accents=3),
    "left_arm": dict(max_colors=5, max_components=2, z=27000, accents=2),
    "right_arm": dict(max_colors=5, max_components=2, z=27020, accents=2),
    "face": dict(max_colors=3, max_components=1, z=28200, accents=0),
}



def _macro_layer(part_name: str, *, accent: bool) -> str:
    if part_name == "hair":
        return "character_hair_detail" if accent else "character_hair_base"
    if part_name == "outfit":
        return "character_outfit_detail" if accent else "character_outfit_base"
    if part_name == "face":
        return "character_body_detail"
    return "character_body_detail" if accent else "character_body_base"

def _prioritize_outfit_groups(groups, face_ref):
    if len(groups) <= 1 or face_ref is None:
        return groups
    max_count = max((count for _, _, count in groups), default=1)
    enriched = []
    for group in groups:
        color, _, count = group
        rgb = np.asarray(color, dtype=np.uint8).reshape(1, 1, 3)
        lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
        contrast = min(1.0, float(np.linalg.norm(lab - face_ref)) / 42.0)
        chroma = min(1.0, float(np.std(np.asarray(color, dtype=np.float32))) / 60.0)
        usage = float(count) / max(float(max_count), 1.0)
        base_score = 0.35 * usage + 0.50 * contrast + 0.15 * chroma
        enriched.append((group, lab, chroma, usage, base_score))
    base_item = max(enriched, key=lambda item: item[4])
    base_group, base_lab, _, _, _ = base_item
    accents = []
    for item in enriched:
        if item is base_item:
            continue
        group, lab, chroma, usage, _ = item
        separation = min(1.0, float(np.linalg.norm(lab - base_lab)) / 48.0)
        feature_score = 0.45 * separation + 0.40 * chroma + 0.15 * usage
        accents.append((feature_score, group))
    accents.sort(key=lambda item: item[0], reverse=True)
    return [base_group] + [group for _, group in accents]


def _keep_existing_detail(shape: Shape) -> bool:
    tags = " ".join(
        [
            str(shape.semantic_type or ""),
            str(shape.character_part or ""),
            str(shape.source_role or ""),
            str(shape.layer_name or ""),
        ]
    ).lower()
    return any(
        token in tags
        for token in (
            "prop",
            "sword",
            "staff",
            "hand",
            "accent",
        )
    )


def build_rinka_macro_partition(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    existing_shapes: list[Shape],
) -> tuple[list[Shape], RinkaMacroReport]:
    required = {"face", "hair", "outfit", "left_arm", "right_arm"}
    available = {str(p.part_type) for p in structure.parts}
    if not required.issubset(available):
        return existing_shapes, RinkaMacroReport(False, "part_gate")
    generated: list[Shape] = []
    counts: dict[str, int] = {}
    tree = build_semantic_shape_tree(structure)
    primitive_fits: dict[str, dict] = {}
    next_id = 795000
    image_lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB).astype(np.float32)
    face_part = _part(structure, "face")
    hair_part = _part(structure, "hair")
    face_ref = None
    hair_ref = None
    if face_part is not None and np.any(face_part.mask):
        face_ref = np.median(image_lab[face_part.mask > 0], axis=0)
    if hair_part is not None and np.any(hair_part.mask):
        hair_ref = np.median(image_lab[hair_part.mask > 0], axis=0)
    for part_name, spec in _PART_SPECS.items():
        part = _part(structure, part_name)
        if part is None or part.mask is None or not np.any(part.mask):
            continue
        effective_mask = (part.mask > 0).astype(np.uint8)
        if part_name == "outfit":
            for exclusion_name in ("face", "hair", "left_arm", "right_arm"):
                exclusion = _part(structure, exclusion_name)
                if exclusion is not None and exclusion.mask is not None:
                    effective_mask[exclusion.mask > 0] = 0
            if face_ref is not None:
                skin_distance = np.linalg.norm(image_lab - face_ref[None, None, :], axis=2)
                effective_mask[skin_distance < 22.0] = 0
            if hair_ref is not None:
                hair_distance = np.linalg.norm(image_lab - hair_ref[None, None, :], axis=2)
                effective_mask[hair_distance < 15.0] = 0
        groups = _coarse_color_groups(
            image_rgb,
            effective_mask,
            max_colors=int(spec["max_colors"]),
            min_fraction=(0.012 if part_name == "outfit" else 0.035),
        )
        if part_name == "outfit":
            groups = _prioritize_outfit_groups(groups, face_ref)
        part_count = 0
        part_area = max(float(np.count_nonzero(effective_mask)), 1.0)
        if not groups:
            counts[part_name] = 0
            continue
        base_color = groups[0][0]
        base_mask = np.zeros_like(effective_mask)
        for _, group_mask, _ in groups:
            base_mask = np.maximum(base_mask, group_mask)
        base_mask = cv2.morphologyEx(base_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        tree_node = tree.get(part_name)
        primitive_budget = max(1, int(tree_node.primitive_budget if tree_node else 1))
        base_contours = _largest_contours(
            base_mask,
            max_components=min(int(spec["max_components"]), primitive_budget),
            min_area=max(8.0, part_area * 0.020),
        )
        for component_index, contour in enumerate(base_contours):
            component_mask = np.zeros_like(base_mask)
            cv2.drawContours(component_mask, [contour], -1, 1, thickness=-1)
            fit, fit_trials = _fit_part_primitive(part_name, component_mask)
            shape_kwargs = dict(
                id=next_id,
                fill_color=base_color,
                z_index=int(spec["z"]) + component_index,
                importance=1.0,
                semantic_type=f"rinka_macro_{part_name}",
                character_part=part_name,
                source_role=f"rinka_macro:{part_name}:base",
                layer_name=_macro_layer(part_name, accent=False),
                part_confidence=0.98,
            )
            if fit is not None:
                shape = _shape_from_fit(fit, **shape_kwargs)
                primitive_fits[f"{part_name}:{component_index}"] = {
                    "selected": fit.to_dict(),
                    "trials": fit_trials,
                }
            else:
                shape = _shape_from_contour(contour, shape_id=next_id, color=base_color,
                    z_index=int(spec["z"]) + component_index,
                    semantic_type=f"rinka_macro_{part_name}", character_part=part_name,
                    source_role=f"rinka_macro:{part_name}:base", layer_name=_macro_layer(part_name, accent=False))
            next_id += 1
            if shape is not None:
                generated.append(shape)
                part_count += 1
        accent_limit = min(max(0, int(spec.get("accents", 0))), max(0, primitive_budget - part_count))
        for group_index, (color, color_mask, _) in enumerate(groups[1 : 1 + accent_limit], start=1):
            contours = _largest_contours(
                color_mask,
                max_components=int(spec["max_components"]),
                min_area=max(6.0, part_area * (0.012 if part_name == "outfit" else 0.035)),
            )
            for component_index, contour in enumerate(contours):
                shape = _shape_from_contour(
                    contour,
                    shape_id=next_id,
                    color=color,
                    z_index=int(spec["z"]) + 8 + group_index * 4 + component_index,
                    semantic_type=f"rinka_macro_{part_name}_accent",
                    character_part=part_name,
                    source_role=f"rinka_macro:{part_name}:accent",
                    layer_name=_macro_layer(part_name, accent=True),
                )
                next_id += 1
                if shape is not None:
                    generated.append(shape)
                    part_count += 1
        counts[part_name] = part_count

    head_feature_shapes, head_feature_report = build_head_feature_shapes(
        image_rgb,
        structure,
        start_id=796000,
    )
    if head_feature_report.enabled:
        generated.extend(head_feature_shapes)
        counts["accessory"] = len(head_feature_shapes)
        tree.add_synthetic(
            "accessory",
            parent="head",
            primitive_budget=3,
            merge_group="accessory",
            protected=True,
            metadata=head_feature_report.to_dict(),
        )
    else:
        counts["accessory"] = 0

    if counts.get("face", 0) < 1 or counts.get("outfit", 0) < 1:
        return existing_shapes, RinkaMacroReport(False, "macro_gate", part_shape_counts=counts)
    retained = [shape for shape in existing_shapes if _keep_existing_detail(shape)]
    out = generated + retained
    out.sort(key=lambda shape: shape.z_index)
    return out, RinkaMacroReport(
        True,
        "accepted",
        generated_shapes=len(generated),
        retained_detail_shapes=len(retained),
        part_shape_counts=counts,
        semantic_tree_nodes=len(tree.nodes),
        primitive_fits=primitive_fits,
        semantic_tree=tree.to_dict(),
        head_features=head_feature_report.to_dict(),
    )
