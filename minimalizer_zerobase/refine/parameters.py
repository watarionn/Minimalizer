from __future__ import annotations
from copy import deepcopy
from dataclasses import replace
import torch
from minimalizer_zerobase.compose import VectorScene

def primitive_tensor(primitive, *, requires_grad: bool = True) -> torch.Tensor:
    p = primitive.parameters
    if primitive.primitive_type == "rectangle":
        values = p["bbox"]
    elif primitive.primitive_type == "ellipse":
        values = (p["cx"], p["cy"], p["rx"], p["ry"])
    else:
        raise ValueError(f"unsupported differentiable primitive: {primitive.primitive_type}")
    return torch.tensor([float(v) for v in values], dtype=torch.float32, requires_grad=requires_grad)

def replace_primitive_parameters(scene: VectorScene, primitive_id: str, values: torch.Tensor) -> VectorScene:
    vals = [float(v) for v in values.detach().cpu()]
    out = []
    found = False
    for primitive in scene.primitives:
        if primitive.primitive_id != primitive_id:
            out.append(primitive); continue
        found = True
        p = deepcopy(primitive.parameters)
        if primitive.primitive_type == "rectangle":
            p["bbox"] = vals
        elif primitive.primitive_type == "ellipse":
            p.update(cx=vals[0], cy=vals[1], rx=vals[2], ry=vals[3])
        else:
            raise ValueError(f"unsupported differentiable primitive: {primitive.primitive_type}")
        out.append(replace(primitive, parameters=p))
    if not found:
        raise KeyError(primitive_id)
    return replace(scene, primitives=tuple(out))
