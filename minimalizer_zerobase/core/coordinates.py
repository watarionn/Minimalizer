from __future__ import annotations
from dataclasses import dataclass
from typing import Literal
from .serialization import CanonicalModel

@dataclass(frozen=True)
class CoordinateSpace(CanonicalModel):
    width: int
    height: int
    unit: Literal["pixel", "normalized"] = "pixel"
    origin: Literal["top_left"] = "top_left"

    def __post_init__(self) -> None:
        if self.width <= 0 or self.height <= 0: raise ValueError("width/height must be positive")

    def normalize_point(self, x: float, y: float) -> tuple[float, float]:
        if self.unit == "normalized": return (x, y)
        return (x / self.width, y / self.height)

    def denormalize_point(self, x: float, y: float) -> tuple[float, float]:
        if self.unit == "pixel": return (x, y)
        return (x * self.width, y * self.height)
