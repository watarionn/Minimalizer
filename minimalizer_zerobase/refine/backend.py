from __future__ import annotations
from typing import Mapping, Protocol

class GeometryGradientBackend(Protocol):
    """Optional renderer/gradient boundary. Backends observe and optimize existing geometry only."""
    name: str
    def step(self, parameters: Mapping[str, float]) -> Mapping[str, float]: ...

def backend_available(name: str) -> bool:
    if name == "diffvg":
        try:
            import pydiffvg  # type: ignore # noqa: F401
        except ImportError:
            return False
        return True
    return False
