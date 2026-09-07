from __future__ import annotations

from dataclasses import dataclass, field
import math

import cv2
import numpy as np

from ..models import Shape
from .body_rules import CharacterBodyAnalysis, LimbPrimitiveDescriptor
from .hand_rules import HandPrimitiveAnalysis, HandPrimitiveDescriptor, _oriented_polygon
from .models import CharacterStructure
from .part_types import CharacterPartType


@dataclass(slots=True)
class HandGeometryItem:
    side: str
    intent: str
    score: float
    connection_score: float
    direction_score: float
    source_center_score: float
    prop_contact_score: float
    corrected: bool
    before_center: tuple[float, float]
    after_center: tuple[float, float]
    before_angle_deg: float
    after_angle_deg: float
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "side": self.side,
            "intent": self.intent,
            "score": self.score,
            "connection_score": self.connection_score,
            "direction_score": self.direction_score,
            "source_center_score": self.source_center_score,
            "prop_contact_score": self.prop_contact_score,
            "corrected": self.corrected,
            "before_center": list(self.before_center),
            "after_center": list(self.after_center),
            "before_angle_deg": self.before_angle_deg,
            "after_angle_deg": self.after_angle_deg,
            "diagnostics": self.diagnostics,
        }


@dataclass(slots=True)
class HandGeometryReport:
    score: float
    hands: list[HandGeometryItem]
    corrected_count: int
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "hands": [h.to_dict() for h in self.hands],
            "corrected_count": self.corrected_count,
            "diagnostics": self.diagnostics,
        }


def _shape_center(shape: Shape) -> tuple[float, float]:
    pts = np.asarray(shape.points, dtype=np.float32)
    if len(pts) == 0:
        return (0.0, 0.0)
    return (float(np.mean(pts[:, 0])), float(np.mean(pts[:, 1])))


def _descriptor_for_side(body: CharacterBodyAnalysis, side: str) -> LimbPrimitiveDescriptor | None:
    want = CharacterPartType.LEFT_ARM if side == "left" else CharacterPartType.RIGHT_ARM
    for d in body.limbs:
        if d.part_type == want:
            return d
    return None


def _hand_for_side(analysis: HandPrimitiveAnalysis, side: str) -> HandPrimitiveDescriptor | None:
    items = [h for h in analysis.hands if h.side == side]
    return max(items, key=lambda h: h.confidence) if items else None


def _polygon_mask(points: list[tuple[float, float]], shape_hw: tuple[int, int]) -> np.ndarray:
    mask = np.zeros(shape_hw, dtype=np.uint8)
    if len(points) >= 3:
        pts = np.asarray(points, dtype=np.int32)
        cv2.fillPoly(mask, [pts], 255)
    return mask


def _connection_score(points: list[tuple[float, float]], distal: tuple[float, float], width: float) -> float:
    if len(points) < 3:
        return 0.0
    contour = np.asarray(points, dtype=np.float32).reshape(-1, 1, 2)
    d = abs(float(cv2.pointPolygonTest(contour, distal, True)))
    inside = cv2.pointPolygonTest(contour, distal, False) >= 0
    if inside:
        return 1.0
    norm = max(2.0, float(width) * 0.75)
    return float(np.clip(math.exp(-d / norm * 1.7), 0.0, 1.0))


def _direction_score(center: tuple[float, float], desc: LimbPrimitiveDescriptor, intent: str) -> float:
    distal = np.asarray(desc.distal, dtype=np.float32)
    bend = np.asarray(desc.bend, dtype=np.float32)
    arm = distal - bend
    hand = np.asarray(center, dtype=np.float32) - distal
    na, nh = float(np.linalg.norm(arm)), float(np.linalg.norm(hand))
    if na < 1e-5 or nh < 1e-5:
        return 0.82
    cos = float(np.clip(np.dot(arm, hand) / (na * nh), -1.0, 1.0))
    base = (cos + 1.0) * 0.5
    if intent in {"open", "compact", "unknown"}:
        base = 0.58 + 0.42 * base
    return float(np.clip(base, 0.0, 1.0))


def _source_center_score(center: tuple[float, float], hand: HandPrimitiveDescriptor) -> float:
    d = float(np.linalg.norm(np.asarray(center) - np.asarray(hand.center)))
    scale = max(4.0, max(hand.width, hand.height) * 0.65)
    return float(np.clip(math.exp(-d / scale * 1.45), 0.0, 1.0))


def _nearest_prop_target(structure: CharacterStructure, origin: tuple[float, float]) -> tuple[np.ndarray | None, float]:
    props = structure.get_parts(CharacterPartType.PROP)
    if not props:
        return None, float("inf")
    o = np.asarray(origin, dtype=np.float32)
    best, best_d = None, float("inf")
    for p in props:
        c = np.asarray(p.centroid, dtype=np.float32)
        d = float(np.linalg.norm(c - o))
        if d < best_d:
            best, best_d = c, d
    return best, best_d


def _prop_contact_score(shape: Shape, structure: CharacterStructure, shape_hw: tuple[int, int]) -> float:
    props = structure.get_parts(CharacterPartType.PROP)
    if not props:
        return 0.0
    sm = _polygon_mask(shape.points, shape_hw)
    if np.count_nonzero(sm) == 0:
        return 0.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    sd = cv2.dilate(sm, k)
    best = 0.0
    for p in props:
        inter = np.count_nonzero((sd > 0) & (p.mask > 0))
        denom = max(1, min(np.count_nonzero(sd), np.count_nonzero(p.mask)))
        best = max(best, min(1.0, inter / denom * 2.2))
    return float(best)


def _dimensions(hand: HandPrimitiveDescriptor) -> tuple[float, float]:
    major = float(np.clip(max(hand.width, hand.height) * 1.08, 4.0, 22.0))
    minor = float(np.clip(min(hand.width, hand.height) * 1.12, 3.5, 16.0))
    if hand.intent == "open":
        return major, max(minor, major * 0.66)
    if hand.intent == "extended":
        return major * 1.18, min(minor, major * 0.48)
    if hand.intent == "holding":
        return major * 0.88, max(minor, major * 0.62)
    if hand.intent == "compact":
        return major * 0.78, max(minor, major * 0.72)
    return major * 0.82, max(minor, major * 0.62)


def _target_geometry(
    hand: HandPrimitiveDescriptor,
    desc: LimbPrimitiveDescriptor,
    structure: CharacterStructure,
) -> tuple[tuple[float, float], float, dict]:
    distal = np.asarray(desc.distal, dtype=np.float32)
    bend = np.asarray(desc.bend, dtype=np.float32)
    arm = distal - bend
    arm /= max(float(np.linalg.norm(arm)), 1e-6)
    along, _ = _dimensions(hand)

    target_axis = arm.copy()
    prop_target, prop_dist = _nearest_prop_target(structure, desc.distal)
    used_prop = False
    if hand.intent == "holding" and prop_target is not None and prop_dist <= max(28.0, along * 3.0):
        v = prop_target - distal
        if np.linalg.norm(v) > 1e-5:
            target_axis = v / np.linalg.norm(v)
            used_prop = True

    target_center = distal + target_axis * along * (0.16 if hand.intent == "holding" else 0.18)
    source_center = np.asarray(hand.center, dtype=np.float32)
    # Preserve source evidence, but anchor the rendered mass to the arm tip.
    blend = 0.72 if hand.intent in {"extended", "holding"} else 0.62
    center = source_center * (1.0 - blend) + target_center * blend
    max_shift = max(5.0, along * 0.48)
    delta = center - source_center
    dn = float(np.linalg.norm(delta))
    if dn > max_shift:
        center = source_center + delta / dn * max_shift

    angle = float(math.degrees(math.atan2(target_axis[1], target_axis[0])))
    return (float(center[0]), float(center[1])), angle, {
        "used_prop_direction": used_prop,
        "nearest_prop_distance": None if not math.isfinite(prop_dist) else float(prop_dist),
        "target_center": [float(v) for v in target_center],
    }


def validate_and_refine_hand_geometry(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    body_analysis: CharacterBodyAnalysis,
    hand_analysis: HandPrimitiveAnalysis,
    hand_shapes: list[Shape],
    *,
    min_connection: float = 0.72,
    min_direction: float = 0.58,
    min_holding_contact: float = 0.45,
) -> tuple[list[Shape], HandGeometryReport]:
    """Anchor 1-Shape hands to arm tips and validate gesture continuity.

    Phase 11.3 is intentionally geometric. It does not add fingers or extra
    shapes. Corrections are translation/orientation changes of an existing
    hand mass only.
    """
    refined: list[Shape] = []
    items: list[HandGeometryItem] = []
    h, w = image_rgb.shape[:2]

    for shape in hand_shapes:
        side = shape.side_hint
        hand = _hand_for_side(hand_analysis, side)
        desc = _descriptor_for_side(body_analysis, side)
        if hand is None or desc is None:
            refined.append(shape)
            continue

        before_center = _shape_center(shape)
        before_conn = _connection_score(shape.points, desc.distal, desc.distal_width)
        before_dir = _direction_score(before_center, desc, hand.intent)
        before_prop = _prop_contact_score(shape, structure, (h, w)) if hand.intent == "holding" else 1.0

        needs_fix = (
            before_conn < min_connection
            or before_dir < min_direction
            or (hand.intent == "holding" and before_prop < min_holding_contact)
        )

        new_shape = shape
        target_meta = {}
        after_angle = float(hand.angle_deg)
        if needs_fix:
            center, after_angle, target_meta = _target_geometry(hand, desc, structure)
            along, across = _dimensions(hand)
            points = _oriented_polygon(center, after_angle, along, across, kind=hand.intent)
            new_shape = Shape(**{**shape.__dict__, "points": points})

        after_center = _shape_center(new_shape)
        conn = _connection_score(new_shape.points, desc.distal, desc.distal_width)
        direction = _direction_score(after_center, desc, hand.intent)
        source_center = _source_center_score(after_center, hand)
        prop = _prop_contact_score(new_shape, structure, (h, w)) if hand.intent == "holding" else 1.0

        weights = [(conn, 0.42), (direction, 0.24), (source_center, 0.20)]
        if hand.intent == "holding":
            weights.append((prop, 0.14))
        else:
            weights.append((1.0, 0.14))
        score = float(sum(v * wt for v, wt in weights) / sum(wt for _, wt in weights))

        items.append(HandGeometryItem(
            side=side,
            intent=hand.intent,
            score=score,
            connection_score=conn,
            direction_score=direction,
            source_center_score=source_center,
            prop_contact_score=prop,
            corrected=bool(needs_fix),
            before_center=before_center,
            after_center=after_center,
            before_angle_deg=float(hand.angle_deg),
            after_angle_deg=after_angle,
            diagnostics={
                "before_connection_score": before_conn,
                "before_direction_score": before_dir,
                "before_prop_contact_score": before_prop,
                **target_meta,
            },
        ))
        refined.append(new_shape)

    overall = float(np.mean([x.score for x in items])) if items else 1.0
    return refined, HandGeometryReport(
        score=overall,
        hands=items,
        corrected_count=sum(1 for x in items if x.corrected),
        diagnostics={
            "phase": "11.3",
            "principle": "connect gesture mass to arm without adding finger detail",
            "evaluated_hand_count": len(items),
            "thresholds": {
                "connection": min_connection,
                "direction": min_direction,
                "holding_contact": min_holding_contact,
            },
        },
    )
