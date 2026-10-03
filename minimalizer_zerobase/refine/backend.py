from __future__ import annotations
from typing import Protocol
import torch

class DifferentiableRasterBackend(Protocol):
    def rectangle(self, bbox: torch.Tensor, width: int, height: int) -> torch.Tensor: ...
    def ellipse(self, params: torch.Tensor, width: int, height: int) -> torch.Tensor: ...

class TorchSoftRasterBackend:
    """Research-only analytic rasterizer used to validate the optimizer boundary."""
    def __init__(self, sharpness: float = 0.35):
        self.sharpness = float(sharpness)

    def _grid(self, width: int, height: int, ref: torch.Tensor):
        y = torch.arange(height, dtype=ref.dtype, device=ref.device) + 0.5
        x = torch.arange(width, dtype=ref.dtype, device=ref.device) + 0.5
        return torch.meshgrid(y, x, indexing="ij")

    def rectangle(self, bbox: torch.Tensor, width: int, height: int) -> torch.Tensor:
        x, y, w, h = bbox
        gy, gx = self._grid(width, height, bbox)
        k = self.sharpness
        return (torch.sigmoid(k*(gx-x))*torch.sigmoid(k*(x+w-gx))*
                torch.sigmoid(k*(gy-y))*torch.sigmoid(k*(y+h-gy)))

    def ellipse(self, params: torch.Tensor, width: int, height: int) -> torch.Tensor:
        cx, cy, rx, ry = params
        gy, gx = self._grid(width, height, params)
        rx = rx.clamp_min(1e-3); ry = ry.clamp_min(1e-3)
        level = 1.0 - ((gx-cx)/rx)**2 - ((gy-cy)/ry)**2
        return torch.sigmoid(self.sharpness*level)

def backend_available(name: str) -> bool:
    if name == "diffvg":
        try:
            import pydiffvg  # type: ignore # noqa: F401
        except ImportError:
            return False
        return True
    return name == "torch-soft"
