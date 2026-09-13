from __future__ import annotations

from dataclasses import dataclass

from .models import Shape


@dataclass(frozen=True)
class StructureCandidateGateResult:
    passed: bool
    reasons: tuple[str, ...] = ()
    shape_count: int = 0
    hair_count: int = 0
    face_count: int = 0
    body_zone_count: int = 0
    carrier_exposure_ratio: float = 0.0
    carrier_patch_count: int = 0

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "reasons": list(self.reasons),
            "shape_count": self.shape_count,
            "hair_count": self.hair_count,
            "face_count": self.face_count,
            "body_zone_count": self.body_zone_count,
            "carrier_exposure_ratio": round(float(self.carrier_exposure_ratio), 6),
            "carrier_patch_count": self.carrier_patch_count,
        }

def evaluate_structure_candidate(
    *,
    structure_enabled: bool,
    face_enabled: bool,
    head_enabled: bool,
    alpha_enabled: bool,
    shapes: tuple[Shape, ...],
    carrier_exposure_ratio: float,
    carrier_patch_count: int,
) -> StructureCandidateGateResult:
    roles = [shape.source_role or "" for shape in shapes]
    hair_count = sum(role.startswith("phase17_alpha_hair_") for role in roles)
    face_count = sum(role == "phase17_alpha_blank_face" for role in roles)
    body_zone_count = sum(role.startswith("phase17_body_zone_") for role in roles)
    full_carrier = any(role == "phase17_alpha_carrier" for role in roles)

    reasons: list[str] = []
    if not structure_enabled:
        reasons.append("structure_missing")
    if not face_enabled:
        reasons.append("face_missing")
    if not head_enabled:
        reasons.append("head_missing")
    if not alpha_enabled:
        reasons.append("alpha_structure_missing")
    structural_shape_count = sum(
        not role.startswith("phase17_carrier_patch") for role in roles
    )
    if not 4 <= structural_shape_count <= 12:
        reasons.append("shape_count_gate")
    if not 1 <= hair_count <= 3:
        reasons.append("hair_count_gate")
    if face_count != 1:
        reasons.append("face_count_gate")
    if body_zone_count < 2:
        reasons.append("body_zone_gate")
    if full_carrier:
        reasons.append("full_carrier_forbidden")
    if carrier_exposure_ratio > 0.30:
        reasons.append("carrier_exposure_gate")
    if carrier_patch_count > 6:
        reasons.append("carrier_patch_gate")

    return StructureCandidateGateResult(
        passed=not reasons,
        reasons=tuple(reasons),
        shape_count=structural_shape_count,
        hair_count=hair_count,
        face_count=face_count,
        body_zone_count=body_zone_count,
        carrier_exposure_ratio=carrier_exposure_ratio,
        carrier_patch_count=carrier_patch_count,
    )
