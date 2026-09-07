from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .hand_rules import HandPrimitiveAnalysis, HandPrimitiveDescriptor


@dataclass(slots=True)
class HandValidationItem:
    side: str
    intent: str
    score: float
    accepted: bool
    reasons: list[str]
    components: dict[str, float] = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "side": self.side,
            "intent": self.intent,
            "score": self.score,
            "accepted": self.accepted,
            "reasons": list(self.reasons),
            "components": dict(self.components),
            "diagnostics": self.diagnostics,
        }


@dataclass(slots=True)
class HandValidationReport:
    score: float
    accepted_hands: list[HandPrimitiveDescriptor]
    rejected_hands: list[HandPrimitiveDescriptor]
    items: list[HandValidationItem]
    diagnostics: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "score": self.score,
            "accepted_count": len(self.accepted_hands),
            "rejected_count": len(self.rejected_hands),
            "accepted_sides": [h.side for h in self.accepted_hands],
            "rejected_sides": [h.side for h in self.rejected_hands],
            "items": [item.to_dict() for item in self.items],
            "diagnostics": self.diagnostics,
        }


def _score_hand(hand: HandPrimitiveDescriptor) -> tuple[float, dict[str, float], list[str]]:
    x, y, w, h = hand.bbox
    min_dim = float(min(w, h))
    max_dim = float(max(w, h))
    area = float(max(1, w * h))
    mask_pixels = float(hand.diagnostics.get("hand_mask_pixels", 0))
    arm_tip_pixels = float(hand.diagnostics.get("arm_tip_pixels", 0))

    confidence = float(np.clip(hand.confidence, 0.0, 1.0))
    skin = float(np.clip(hand.skin_ratio, 0.0, 1.0))
    prop = float(np.clip(hand.prop_contact, 0.0, 1.0))
    geometry = float(np.clip(0.55 * hand.solidity + 0.45 * min(1.0, hand.extent / 0.62), 0.0, 1.0))
    continuity = float(np.clip(mask_pixels / max(6.0, arm_tip_pixels * 0.72), 0.0, 1.0))
    size = float(np.clip((min_dim - 1.0) / 5.0, 0.0, 1.0))

    # A glove can be a valid hand with little skin evidence. Therefore skin is
    # supporting evidence, never a hard requirement. Prop contact is strong
    # evidence for a holding hand.
    score = (
        confidence * 0.34
        + skin * 0.16
        + geometry * 0.18
        + continuity * 0.15
        + size * 0.10
        + prop * 0.16
    )

    reasons: list[str] = []
    if min_dim <= 1.5:
        score -= 0.30
        reasons.append("too_thin_for_hand")
    elif min_dim <= 2.5:
        score -= 0.14
        reasons.append("very_thin_candidate")
    if area <= 10.0:
        score -= 0.12
        reasons.append("tiny_candidate")
    if hand.intent == "unknown":
        score -= 0.10
        reasons.append("unknown_intent")
    if skin < 0.03 and prop < 0.12 and confidence < 0.47:
        score -= 0.09
        reasons.append("weak_appearance_evidence")
    if hand.intent == "open" and min_dim <= 2.5:
        score -= 0.10
        reasons.append("open_hand_too_narrow")
    if max_dim > 34.0 and hand.intent != "holding":
        score -= 0.06
        reasons.append("oversized_tip_mass")

    components = {
        "confidence": confidence,
        "skin_support": skin,
        "geometry_support": geometry,
        "arm_tip_continuity": continuity,
        "size_support": size,
        "prop_support": prop,
    }
    return float(np.clip(score, 0.0, 1.0)), components, reasons


def validate_hand_candidates(
    analysis: HandPrimitiveAnalysis,
    *,
    min_score: float = 0.42,
    unknown_min_score: float = 0.42,
) -> HandValidationReport:
    """Suppress weak sleeve/hair/accessory tips before hand Shape rendering.

    The validator is deliberately conservative: skin is optional because gloves
    are common, while extremely thin/tiny distal masses and low-evidence unknown
    gestures are treated as likely false hands.
    """
    accepted: list[HandPrimitiveDescriptor] = []
    rejected: list[HandPrimitiveDescriptor] = []
    items: list[HandValidationItem] = []

    for hand in analysis.hands:
        score, components, reasons = _score_hand(hand)
        threshold = float(unknown_min_score if hand.intent == "unknown" else min_score)
        accepted_flag = bool(score >= threshold)
        if hand.intent == "holding" and hand.prop_contact >= 0.45 and score >= min_score - 0.08:
            accepted_flag = True
            reasons.append("holding_prop_rescue")
        if accepted_flag:
            accepted.append(hand)
        else:
            rejected.append(hand)
            reasons.append("below_validation_threshold")
        items.append(
            HandValidationItem(
                side=hand.side,
                intent=hand.intent,
                score=score,
                accepted=accepted_flag,
                reasons=reasons,
                components=components,
                diagnostics={"threshold": threshold, "bbox": list(hand.bbox)},
            )
        )

    report_score = float(np.mean([item.score for item in items])) if items else 1.0
    return HandValidationReport(
        score=report_score,
        accepted_hands=accepted,
        rejected_hands=rejected,
        items=items,
        diagnostics={
            "phase": "11.4",
            "purpose": "false_hand_suppression",
            "rendering_changed": bool(rejected),
            "min_score": float(min_score),
            "unknown_min_score": float(unknown_min_score),
            "input_count": len(analysis.hands),
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
        },
    )


def filtered_hand_analysis(
    analysis: HandPrimitiveAnalysis,
    report: HandValidationReport,
) -> HandPrimitiveAnalysis:
    """Return an analysis view containing only validated hand candidates."""
    hands = list(report.accepted_hands)
    confidence = float(np.mean([h.confidence for h in hands])) if hands else 0.0
    diagnostics = dict(analysis.diagnostics)
    diagnostics.update({
        "validated": True,
        "pre_validation_count": len(analysis.hands),
        "detected_hand_count": len(hands),
        "suppressed_hand_count": len(report.rejected_hands),
    })
    return HandPrimitiveAnalysis(hands=hands, confidence=confidence, diagnostics=diagnostics)
