from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

import cv2
import numpy as np

from ..models import Shape
from .body_rules import CharacterBodyAnalysis, LimbPrimitiveDescriptor
from .models import CharacterPartCandidate, CharacterStructure
from .part_types import CharacterPartType

HandIntent = Literal["open", "compact", "extended", "holding", "unknown"]


@dataclass(slots=True)
class HandPrimitiveDescriptor:
    side: str
    intent: HandIntent
    center: tuple[float, float]
    bbox: tuple[int, int, int, int]
    angle_deg: float
    width: float
    height: float
    confidence: float
    skin_ratio: float
    solidity: float
    extent: float
    prop_contact: float
    source_part_type: CharacterPartType
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "side": self.side,
            "intent": self.intent,
            "center": list(self.center),
            "bbox": list(self.bbox),
            "angle_deg": self.angle_deg,
            "width": self.width,
            "height": self.height,
            "confidence": self.confidence,
            "skin_ratio": self.skin_ratio,
            "solidity": self.solidity,
            "extent": self.extent,
            "prop_contact": self.prop_contact,
            "source_part_type": str(self.source_part_type),
            "diagnostics": self.diagnostics,
        }


@dataclass(slots=True)
class HandPrimitiveAnalysis:
    hands: list[HandPrimitiveDescriptor]
    confidence: float
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "hands": [h.to_dict() for h in self.hands],
            "confidence": self.confidence,
            "diagnostics": self.diagnostics,
        }


def _broad_skin_mask(image_rgb: np.ndarray) -> np.ndarray:
    rgb = image_rgb.astype(np.int16)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx = np.max(rgb, axis=2)
    mn = np.min(rgb, axis=2)
    classic = (
        (r >= 120) & (g >= 55) & (b >= 45)
        & ((mx - mn) >= 12)
        & (r >= g - 8) & (r >= b + 4)
    )
    hsv = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    warm = (((h <= 24) | (h >= 168)) & (s >= 18) & (s <= 190) & (v >= 80))
    mask = (classic | warm).astype(np.uint8) * 255
    return cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))


def _limb_part(structure: CharacterStructure, desc: LimbPrimitiveDescriptor) -> CharacterPartCandidate | None:
    return structure.first_part(desc.part_type)


def _prop_contact_score(structure: CharacterStructure, zone: np.ndarray) -> float:
    if np.count_nonzero(zone) == 0:
        return 0.0
    props = structure.get_parts(CharacterPartType.PROP)
    if not props:
        return 0.0
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    zd = cv2.dilate(zone, k)
    best = 0.0
    for prop in props:
        inter = np.count_nonzero((zd > 0) & (prop.mask > 0))
        denom = max(1, min(np.count_nonzero(zd), np.count_nonzero(prop.mask)))
        best = max(best, min(1.0, inter / denom * 2.4))
    return float(best)


def _contour_metrics(mask: np.ndarray) -> tuple[tuple[int, int, int, int], float, float, float, float]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return (0, 0, 0, 0), 0.0, 0.0, 0.0, 0.0
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    area = max(1.0, float(cv2.contourArea(contour)))
    hull = cv2.convexHull(contour)
    hull_area = max(1.0, float(cv2.contourArea(hull)))
    solidity = float(np.clip(area / hull_area, 0.0, 1.0))
    extent = float(np.clip(area / max(1.0, w * h), 0.0, 1.0))
    if len(contour) >= 5:
        (_, _), (rw, rh), angle = cv2.fitEllipse(contour)
        major = max(rw, rh)
        minor = max(1.0, min(rw, rh))
        elong = float(major / minor)
    else:
        elong = float(max(w, h) / max(1, min(w, h)))
        angle = 0.0
    return (x, y, w, h), solidity, extent, elong, float(angle)


def _make_hand_descriptor(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    desc: LimbPrimitiveDescriptor,
    skin_mask: np.ndarray,
) -> HandPrimitiveDescriptor | None:
    part = _limb_part(structure, desc)
    if part is None:
        return None

    h, w = part.mask.shape
    distal = np.asarray(desc.distal, dtype=np.float32)
    bend = np.asarray(desc.bend, dtype=np.float32)
    axis = distal - bend
    axis_len = max(float(np.linalg.norm(axis)), 1.0)
    axis /= axis_len

    radius = max(4.0, min(22.0, desc.distal_width * 1.9 + axis_len * 0.08))
    center = distal + axis * radius * 0.10
    yy, xx = np.ogrid[:h, :w]
    circle = (((xx - center[0]) ** 2 + (yy - center[1]) ** 2) <= radius ** 2).astype(np.uint8) * 255
    local_arm = cv2.bitwise_and((part.mask > 0).astype(np.uint8) * 255, circle)

    # Prefer exposed skin at the distal end, but retain the arm tip when gloves,
    # stylization, or source colors make skin detection unreliable.
    exposed = cv2.bitwise_and(local_arm, skin_mask)
    arm_pixels = np.count_nonzero(local_arm)
    skin_pixels = np.count_nonzero(exposed)
    skin_ratio = float(skin_pixels / max(1, arm_pixels))
    if skin_pixels >= max(6, int(arm_pixels * 0.14)):
        hand_mask = cv2.dilate(exposed, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
        hand_mask = cv2.bitwise_and(hand_mask, circle)
        strategy = "distal_skin"
    else:
        hand_mask = local_arm
        strategy = "distal_tip"

    if np.count_nonzero(hand_mask) < 6:
        return None

    bbox, solidity, extent, elongation, fit_angle = _contour_metrics(hand_mask)
    if bbox[2] <= 0 or bbox[3] <= 0:
        return None
    prop_contact = _prop_contact_score(structure, hand_mask)

    # Semantic intent is deliberately coarse. Minimalizer needs the readable
    # gesture class, not finger-level reconstruction.
    if prop_contact >= 0.18:
        intent: HandIntent = "holding"
    elif elongation >= 1.75 and extent >= 0.32:
        intent = "extended"
    elif solidity >= 0.88 and extent >= 0.58:
        intent = "compact"
    elif solidity <= 0.82 or extent <= 0.46:
        intent = "open"
    else:
        intent = "unknown"

    evidence = 0.28 + min(0.24, arm_pixels / max(1.0, np.pi * radius * radius) * 0.28)
    evidence += min(0.22, skin_ratio * 0.35)
    evidence += min(0.18, prop_contact * 0.32)
    evidence += min(0.12, max(0.0, part.confidence) * 0.16)
    if intent == "unknown":
        evidence *= 0.72
    confidence = float(np.clip(evidence, 0.0, 0.98))

    x, y, bw, bh = bbox
    return HandPrimitiveDescriptor(
        side=desc.side,
        intent=intent,
        center=(float(x + bw / 2.0), float(y + bh / 2.0)),
        bbox=bbox,
        angle_deg=fit_angle,
        width=float(bw),
        height=float(bh),
        confidence=confidence,
        skin_ratio=skin_ratio,
        solidity=solidity,
        extent=extent,
        prop_contact=prop_contact,
        source_part_type=desc.part_type,
        diagnostics={
            "strategy": strategy,
            "radius": float(radius),
            "elongation": elongation,
            "arm_tip_pixels": int(arm_pixels),
            "hand_mask_pixels": int(np.count_nonzero(hand_mask)),
            "distal": [float(v) for v in desc.distal],
            "bend": [float(v) for v in desc.bend],
        },
    )


def analyze_hand_primitives(
    image_rgb: np.ndarray,
    structure: CharacterStructure,
    body_analysis: CharacterBodyAnalysis,
) -> HandPrimitiveAnalysis:
    skin = _broad_skin_mask(image_rgb)
    hands: list[HandPrimitiveDescriptor] = []
    for desc in body_analysis.limbs:
        if desc.part_type not in {CharacterPartType.LEFT_ARM, CharacterPartType.RIGHT_ARM}:
            continue
        item = _make_hand_descriptor(image_rgb, structure, desc, skin)
        if item is not None:
            hands.append(item)

    hands.sort(key=lambda x: (0 if x.side == "left" else 1, -x.confidence))
    confidence = float(np.mean([h.confidence for h in hands])) if hands else 0.0
    return HandPrimitiveAnalysis(
        hands=hands,
        confidence=confidence,
        diagnostics={
            "phase": "11.1",
            "rendering_changed": False,
            "detected_hand_count": len(hands),
            "intent_counts": {
                key: sum(1 for hand in hands if hand.intent == key)
                for key in ["open", "compact", "extended", "holding", "unknown"]
            },
        },
    )



def _sample_hand_color(
    image_rgb: np.ndarray,
    hand: HandPrimitiveDescriptor,
) -> tuple[int, int, int]:
    """Pick one stable flat color from the source hand zone.

    Skin-like pixels are preferred, but gloves/stylized hands fall back to the
    local median so Phase 11.2 does not force a skin tone onto every character.
    """
    h, w = image_rgb.shape[:2]
    x, y, bw, bh = hand.bbox
    pad = max(1, int(round(max(bw, bh) * 0.20)))
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(w, x + bw + pad), min(h, y + bh + pad)
    patch = image_rgb[y0:y1, x0:x1]
    if patch.size == 0:
        return (196, 154, 132)

    skin = _broad_skin_mask(patch) > 0
    pixels = patch[skin] if np.count_nonzero(skin) >= 6 else patch.reshape(-1, 3)
    if len(pixels) > 12:
        lum = pixels.astype(np.float32) @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        lo, hi = np.percentile(lum, [12, 88])
        core = pixels[(lum >= lo) & (lum <= hi)]
        if len(core) >= 6:
            pixels = core
    med = np.median(pixels.astype(np.float32), axis=0)
    return tuple(int(np.clip(round(v), 0, 255)) for v in med)


def _oriented_polygon(
    center: tuple[float, float],
    angle_deg: float,
    along: float,
    across: float,
    *,
    kind: str,
) -> list[tuple[float, float]]:
    """Return a tiny intent-aware hand silhouette as one polygon."""
    theta = np.deg2rad(angle_deg)
    axis = np.array([np.cos(theta), np.sin(theta)], dtype=np.float32)
    perp = np.array([-axis[1], axis[0]], dtype=np.float32)
    c = np.asarray(center, dtype=np.float32)
    a = max(2.0, float(along) * 0.5)
    b = max(1.8, float(across) * 0.5)

    if kind == "open":
        # One broad fan/mitten shape. The tip is intentionally asymmetric so
        # an open palm reads as a gesture without drawing fingers.
        local = [
            (-0.60*a, -0.72*b),
            (0.20*a, -1.00*b),
            (0.88*a, -0.52*b),
            (1.00*a, 0.08*b),
            (0.50*a, 0.78*b),
            (-0.45*a, 0.84*b),
            (-0.90*a, 0.25*b),
        ]
    elif kind == "extended":
        local = [
            (-1.00*a, -0.55*b),
            (0.70*a, -0.62*b),
            (1.00*a, -0.30*b),
            (1.00*a, 0.30*b),
            (0.70*a, 0.62*b),
            (-1.00*a, 0.55*b),
        ]
    elif kind == "holding":
        # Compact grip with a slight forward notch toward the prop/contact.
        local = [
            (-0.90*a, -0.62*b),
            (0.48*a, -0.78*b),
            (1.00*a, -0.20*b),
            (0.72*a, 0.62*b),
            (-0.25*a, 0.82*b),
            (-0.92*a, 0.35*b),
        ]
    else:
        local = [
            (-0.85*a, -0.62*b),
            (0.45*a, -0.78*b),
            (0.92*a, -0.25*b),
            (0.78*a, 0.55*b),
            (-0.20*a, 0.82*b),
            (-0.92*a, 0.25*b),
        ]
    return [tuple((c + axis * lx + perp * ly).tolist()) for lx, ly in local]


def build_hand_shapes(
    image_rgb: np.ndarray,
    analysis: HandPrimitiveAnalysis,
    *,
    start_id: int,
    max_shapes: int = 2,
    min_confidence: float = 0.34,
) -> list[Shape]:
    """Convert coarse hand intent into at most one Shape per detected hand.

    Phase 11.2 deliberately keeps the hand vocabulary tiny. A hand is a single
    readable gesture mass, never a finger-by-finger reconstruction.
    """
    if max_shapes <= 0:
        return []

    candidates = [h for h in analysis.hands if h.confidence >= min_confidence]
    # Keep left/right coverage before confidence-only ranking.
    candidates.sort(key=lambda h: (0 if h.side == "left" else 1, -h.confidence))
    candidates = candidates[:max_shapes]

    out: list[Shape] = []
    for i, hand in enumerate(candidates):
        color = _sample_hand_color(image_rgb, hand)
        x, y, bw, bh = hand.bbox
        # Hand analysis ellipse angle can be noisy on tiny masks. Blend source
        # geometry with bbox dimensions and cap the rendered mass.
        major = float(np.clip(max(hand.width, hand.height) * 1.08, 4.0, 22.0))
        minor = float(np.clip(min(hand.width, hand.height) * 1.12, 3.5, 16.0))
        if hand.intent == "open":
            along, across = major * 1.00, max(minor, major * 0.66)
        elif hand.intent == "extended":
            along, across = major * 1.18, min(minor, major * 0.48)
        elif hand.intent == "holding":
            along, across = major * 0.88, max(minor, major * 0.62)
        elif hand.intent == "compact":
            along, across = major * 0.78, max(minor, major * 0.72)
        else:
            along, across = major * 0.82, max(minor, major * 0.62)

        points = _oriented_polygon(
            hand.center,
            hand.angle_deg,
            along,
            across,
            kind=hand.intent,
        )
        out.append(
            Shape(
                id=start_id + i,
                shape_type="polygon",
                fill_color=color,
                points=points,
                source_role="character_hand_base",
                layer_name="character_body_detail",
                semantic_type=f"character_hand_{hand.intent}",
                character_part=f"{hand.side}_hand",
                part_confidence=hand.confidence,
                side_hint=hand.side,
                importance=0.985,
            )
        )
    return out
