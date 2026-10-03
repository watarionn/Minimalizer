from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticTrustPolicy:
    face: float = 0.45
    head: float = 0.60
    hair: float = 1.50
    major_clothing: float = 2.00
    limb: float = 1.00
    accessory: float = 1.25
    default: float = 1.00
    ownership_weight: float = 12.0

    def radius_for(self, part: str) -> float:
        if part == "face": return self.face
        if part == "head": return self.head
        if part == "hair": return self.hair
        if part == "major_clothing": return self.major_clothing
        if part in ("left_arm","right_arm","lower_body","limb"): return self.limb
        if part in ("accessory","accessory_or_held_object"): return self.accessory
        return self.default
