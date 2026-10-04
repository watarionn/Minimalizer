from __future__ import annotations
from dataclasses import dataclass
import torch
from minimalizer_zerobase.compose import VectorScene
from .backend import DifferentiableRasterBackend, TorchSoftRasterBackend
from .parameters import primitive_tensor, replace_primitive_parameters

@dataclass(frozen=True)
class GeometryRefinement:
    scene: VectorScene
    initial_loss: float
    final_loss: float
    steps: int

def refine_primitive(scene: VectorScene, primitive_id: str, target_mask: torch.Tensor, *,
                     steps: int = 40, learning_rate: float = 0.25,
                     backend: DifferentiableRasterBackend | None = None) -> GeometryRefinement:
    backend = backend or TorchSoftRasterBackend()
    primitive = next((p for p in scene.primitives if p.primitive_id == primitive_id), None)
    if primitive is None:
        raise KeyError(primitive_id)
    values = primitive_tensor(primitive)
    opt = torch.optim.Adam([values], lr=learning_rate)
    initial = None
    for _ in range(steps):
        opt.zero_grad()
        mask = (backend.rectangle(values, scene.width, scene.height)
                if primitive.primitive_type == "rectangle"
                else backend.ellipse(values, scene.width, scene.height))
        loss = ((mask-target_mask)**2).mean()
        if initial is None: initial = loss.detach().item()
        loss.backward()
        if values.grad is None or not torch.isfinite(values.grad).all():
            raise FloatingPointError("non-finite differentiable geometry gradient")
        torch.nn.utils.clip_grad_norm_([values], 1.0)
        opt.step()
        with torch.no_grad():
            if primitive.primitive_type == "rectangle":
                values[0].clamp_(0, scene.width-1); values[1].clamp_(0, scene.height-1)
                values[2].clamp_(1, scene.width); values[3].clamp_(1, scene.height)
            else:
                values[0].clamp_(0, scene.width); values[1].clamp_(0, scene.height)
                values[2].clamp_(1, scene.width/2); values[3].clamp_(1, scene.height/2)
    final_mask = (backend.rectangle(values, scene.width, scene.height)
                  if primitive.primitive_type == "rectangle"
                  else backend.ellipse(values, scene.width, scene.height))
    final = ((final_mask-target_mask)**2).mean().detach().item()
    return GeometryRefinement(replace_primitive_parameters(scene, primitive_id, values), initial or 0.0, final, steps)
